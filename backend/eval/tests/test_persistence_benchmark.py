"""Opt-in measured replacement writes of the frozen public 938-vector fixture."""

import hashlib
import json
import os
import statistics
import sys
import time
import types
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import event, text
from testcontainers.community.postgres import PostgresContainer

from app.core.database import get_session_factory, tenant_session
from app.features.documents.storage import DocumentStorage
from app.features.documents.tests.test_upload import profile_for
from app.features.ingestion.chunking.chunker import Chunk
from app.features.ingestion.parsers.base import Box, ParsedPage
from app.features.ingestion.pipeline import IngestionPipeline
from app.features.tenancy.context import TenantContext
from conftest import IMAGE, MAX_LOCKS_PER_TRANSACTION, Account

pytestmark = pytest.mark.skipif(
    not os.environ.get("ZENITH_RUN_PERSISTENCE_BENCHMARK"), reason="opt-in persistence measurement"
)


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with (
        PostgresContainer(IMAGE, driver="psycopg")
        .with_command(f"postgres -c max_locks_per_transaction={MAX_LOCKS_PER_TRANSACTION}")
        .with_kwargs(mem_limit="768m", nano_cpus=2_000_000_000)
    ) as container:
        yield container


async def test_public_persistence_profile(account: Account, tmp_path: Path) -> None:
    from app.features.documents.service import DocumentService

    fixture_path = Path(os.environ["ZENITH_PERSISTENCE_FIXTURE"])
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert len(fixture["chunks"]) == 938
    assert all(len(row["vector"]) == 1024 for row in fixture["chunks"])
    pages = [ParsedPage(**row) for row in fixture["pages"]]
    chunks = [
        Chunk(
            page_num=row["page_num"],
            char_start=row["char_start"],
            char_end=row["char_end"],
            text=row["text"],
            boxes=tuple(Box(**box) for box in row["bboxes"]),
            section=row["section"],
        )
        for row in fixture["chunks"]
    ]
    vectors = [row["vector"] for row in fixture["chunks"]]
    content = pages[0].text.encode()
    assert hashlib.sha256(content).hexdigest() == fixture["document_sha256"]

    async def stream() -> AsyncIterator[bytes]:
        yield content

    storage = DocumentStorage(root=tmp_path)
    result = await DocumentService(await profile_for(account), storage).upload(
        "public-persistence.txt", stream(), label_ids=[account.default_label]
    )
    context = TenantContext.for_tenant(account.tenant_id, result.labels)
    document_id = result.document.id
    pipeline = IngestionPipeline(context, storage)
    baseline_path = Path(os.environ["ZENITH_PERSISTENCE_BASELINE"])
    baseline = types.ModuleType("frozen_persistence_baseline")
    sys.modules[baseline.__name__] = baseline
    exec(
        compile(baseline_path.read_text(encoding="utf-8"), str(baseline_path), "exec"),
        baseline.__dict__,
    )
    engine = get_session_factory().kw["bind"].sync_engine
    timings: dict[str, dict[str, float | int]] = {}
    opened: list[float] = []

    def before(*args: Any) -> None:
        opened.append(time.perf_counter())

    def after(
        conn: Any, cursor: Any, statement: str, parameters: Any, execution: Any, many: bool
    ) -> None:
        elapsed = time.perf_counter() - opened.pop()
        normalized = statement.strip().lower()
        if normalized.startswith("insert into"):
            category = "insert_" + normalized.split()[2].split("(")[0]
        elif normalized.startswith("delete from"):
            category = "delete_" + normalized.split()[2]
        else:
            category = normalized.split()[0]
        item = timings.setdefault(category, {"seconds": 0.0, "calls": 0})
        item["seconds"] += elapsed
        item["calls"] += 1

    mode = os.environ.get("ZENITH_PERSISTENCE_MODE", "paired")
    orders = (
        [("baseline",)]
        if mode == "profile"
        else [
            ("baseline", "candidate"),
            ("candidate", "baseline"),
            ("baseline", "candidate"),
            ("candidate", "baseline"),
        ]
    )
    trials: list[dict[str, Any]] = []
    for pair, order in enumerate(orders):
        for arm in order:
            timings, opened = {}, []
            event.listen(engine, "before_cursor_execute", before)
            event.listen(engine, "after_cursor_execute", after)
            started = time.perf_counter()
            try:
                if arm == "baseline":
                    await baseline.IngestionPipeline._persist(
                        pipeline, document_id, pages, chunks, vectors
                    )
                else:
                    await pipeline._persist(document_id, pages, chunks, vectors)  # pyright: ignore[reportPrivateUsage]
            finally:
                elapsed = time.perf_counter() - started
                event.remove(engine, "before_cursor_execute", before)
                event.remove(engine, "after_cursor_execute", after)
            async with tenant_session(context) as session:
                rows = (
                    await session.execute(
                        text(
                            "SELECT c.text, c.label_ids, e.embedding::text AS vector "
                            "FROM chunks c JOIN chunk_embeddings e "
                            "ON e.chunk_id=c.id AND e.tenant_id=c.tenant_id "
                            "WHERE c.document_id=:d ORDER BY c.char_start,c.id"
                        ),
                        {"d": document_id},
                    )
                ).all()
                assert (
                    await session.scalar(
                        text("SELECT status FROM documents WHERE id=:d"), {"d": document_id}
                    )
                    == "classifying"
                )
            assert len(rows) == 938
            assert [row.text for row in rows] == [row["text"] for row in fixture["chunks"]]
            assert all(row.label_ids == list(context.label_ids) for row in rows)
            # pgvector stores float32; compare exact stored float32 representations.
            import numpy as np

            for row, vector in zip(rows, vectors, strict=True):
                assert np.array_equal(
                    np.array(json.loads(row.vector), dtype=np.float32),
                    np.array(vector, dtype=np.float32),
                )
            trials.append(
                {
                    "pair": pair,
                    "arm": arm,
                    "seconds": elapsed,
                    "sql": timings,
                    "first_insert": len(trials) == 0,
                }
            )
            report = {
                "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
                "baseline_source_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                "chunks": 938,
                "dimensions": 1024,
                "database_cpus": 2,
                "database_memory_mib": 768,
                "mode": mode,
                "trials": trials,
                "scope": "isolated application-role atomic replacement; first pair is warmup",
                "summary": {
                    name: {
                        "median_seconds": statistics.median(
                            float(row["seconds"])
                            for row in trials
                            if row["arm"] == name and (mode == "profile" or int(row["pair"]) > 0)
                        )
                    }
                    for name in ("baseline", "candidate")
                    if any(
                        row["arm"] == name and (mode == "profile" or int(row["pair"]) > 0)
                        for row in trials
                    )
                },
            }
            Path(os.environ["ZENITH_PERSISTENCE_OUTPUT"]).write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
            print(
                json.dumps({"arm": arm, "pair": pair, "seconds": elapsed, "sql": timings}),
                flush=True,
            )
