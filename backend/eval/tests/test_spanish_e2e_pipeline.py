"""Opt-in public-corpus uploads, actual retrieval, generation, citations and audit writes."""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import procrastinate
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.community.postgres import PostgresContainer

from app.common.exceptions import ZenithError
from app.core.config import settings
from app.core.database import tenant_session
from app.core.hardware import PROFILES
from app.features.auth.router import router as auth_router
from app.features.documents.router import router as documents_router
from app.features.embeddings.client import TeiClient
from app.features.generation import service as generation
from app.features.generation.answering.citations import MARKER
from app.features.ingestion import tasks
from app.features.ingestion.chunking.chunker import Chunk
from app.features.ingestion.parsers.base import ParsedPage
from app.features.ingestion.pipeline import IngestionPipeline, Result
from app.features.query.router import router as query_router
from app.features.retrieval import service as retrieval
from app.features.retrieval.breaker import Breaker
from app.features.retrieval.judging.protocol import AssessmentBatch
from app.features.retrieval.reranker import Scored, TeiReranker
from app.features.retrieval.router import router as search_router
from app.features.retrieval.search import Hit
from app.features.retrieval.tests.test_search import profile_for
from app.features.tenancy.context import TenantContext
from app.main import handle_domain_error
from conftest import IMAGE, MAX_LOCKS_PER_TRANSACTION, PASSWORD, Account
from conftest import account as seed_account
from eval.e2e_generator import LocalEvaluationProvider
from eval.spanish_e2e import measure, save, spans_supported
from eval.tests.test_local_first_baseline import baseline_client

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not os.environ.get("ZENITH_RUN_SPANISH_E2E"),
        reason="opt-in actual Spanish model evaluation",
    ),
]


@pytest.fixture(scope="session")
def postgres() -> Any:
    """Reuse only the controller's isolated database in this opt-in module."""
    if os.environ.get("ZENITH_E2E_PERSISTENT_DB"):

        class ExistingDatabase:
            username = "test"
            password = "test"
            dbname = "test"

            def get_container_host_ip(self) -> str:
                return "db-e2e"

            def get_exposed_port(self, port: int) -> str:
                assert port == 5432
                return "5432"

        yield ExistingDatabase()
    else:
        with (
            PostgresContainer(IMAGE, driver="psycopg")
            .with_command(f"postgres -c max_locks_per_transaction={MAX_LOCKS_PER_TRANSACTION}")
            .with_kwargs(mem_limit="768m", nano_cpus=2_000_000_000)
        ) as container:
            yield container


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = (
        Path(os.environ["ZENITH_E2E_OUTPUT"]) / "public-documents"
        if os.environ.get("ZENITH_E2E_PERSISTENT_DB")
        else tmp_path / "documents"
    )
    monkeypatch.setattr(settings, "storage_dir", root)


@pytest.fixture
async def account(configured_engines: None) -> Account:
    path = Path(os.environ["ZENITH_E2E_OUTPUT"]) / "account.json"
    if os.environ.get("ZENITH_E2E_PERSISTENT_DB") and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return Account(
            tenant_id=UUID(data["tenant_id"]),
            admin_id=UUID(data["admin_id"]),
            admin_email=str(data["admin_email"]),
            member_id=UUID(data["member_id"]),
            member_email=str(data["member_email"]),
            finance_label=UUID(data["finance_label"]),
            hr_label=UUID(data["hr_label"]),
            default_label=UUID(data["default_label"]),
            quarantine_label=UUID(data["quarantine_label"]),
        )
    seeded = cast(Account, await seed_account.__wrapped__(configured_engines))  # type: ignore[attr-defined]
    if os.environ.get("ZENITH_E2E_PERSISTENT_DB"):
        save(path, json.loads(json.dumps(asdict(seeded), default=str)))
    return seeded


async def await_file(path: Path, deadline: float) -> None:
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError(f"staged evaluation input not delivered: {path.name}")
        await asyncio.sleep(1)


async def test_public_spanish_answers(
    account: Account,
    owner_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    panel_path = Path(os.environ["ZENITH_E2E_PANEL"])
    output = Path(os.environ["ZENITH_E2E_OUTPUT"])
    fixture = json.loads(panel_path.read_text(encoding="utf-8"))
    record: dict[str, Any] = {
        "fixture_sha256": hashlib.sha256(panel_path.read_bytes()).hexdigest(),
        "protocol": fixture["protocol"],
        "phase": "upload",
        "cases": [],
    }
    profile = replace(
        PROFILES["cpu"], rerank_candidates=32, max_batch_tokens=1024, max_client_batch_size=2
    )
    monkeypatch.setattr(settings, "tei_embed_url", "http://embed-e2e:80")
    monkeypatch.setattr(settings, "hardware", "cpu")
    monkeypatch.setitem(PROFILES, "cpu", profile)
    monkeypatch.setattr(retrieval, "active_profile", lambda: profile)
    monkeypatch.setattr("app.features.embeddings.client.active_profile", lambda: profile)
    monkeypatch.delenv("ZENITH_DISABLE_INGESTION_QUEUE", raising=False)
    monkeypatch.setenv("ZENITH_BASELINE_TRANSPORT", "tcp")
    api = FastAPI()
    api.add_exception_handler(ZenithError, handle_domain_error)  # type: ignore[arg-type]
    for router in (auth_router, documents_router, search_router, query_router):
        api.include_router(router)
    vectors: dict[str, list[float]] = {}
    captured: dict[str, list[dict[str, Any]]] = {}
    prior_path = output / "candidates.json"
    prior_cases: dict[str, Any] = {}
    if os.environ.get("ZENITH_E2E_PERSISTENT_DB") and prior_path.exists():
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        if prior["protocol"] != fixture["protocol"]:
            raise ValueError("persistent fixture protocol changed")
        for case in prior["cases"]:
            prior_cases[case["id"]] = case
            vectors[case["question"]] = case["embedding"]
            captured[case["question"]] = case["candidates"]
    current: dict[str, Any] = {"capture": True, "arm": "bge"}
    actual_embed = TeiClient.embed_query
    actual_rerank = retrieval.SearchService._rerank  # pyright: ignore[reportPrivateUsage]

    async def embed(self: TeiClient, question: str) -> list[float]:
        if current["capture"] and question not in vectors:
            vectors[question] = await actual_embed(self, question)
        if question not in vectors:
            raise ValueError("unrecorded query embedding would break the paired experiment")
        return vectors[question]

    async def rerank(
        self: retrieval.SearchService, question: str, hits: list[Hit], limit: int
    ) -> tuple[list[Hit], str | None, AssessmentBatch | None]:
        serialized = json.loads(json.dumps([asdict(hit) for hit in hits], default=str))
        # This internal version hash was added after the frozen public capture. It is
        # neither a ranking input nor a source coordinate. Preserve exact comparison of
        # every original field, including IDs, ranks, scores, order and source text.
        for item in serialized:
            item.pop("source_sha256", None)
        if question in captured and serialized != captured[question]:
            raise ValueError("persistent database retrieval no longer matches its capture")
        if current["capture"]:
            captured[question] = serialized
        elif serialized != captured[question]:
            raise ValueError("retrieval candidates changed between paired model stages")
        ordered, reason, assessment = await actual_rerank(self, question, hits, limit)
        current["shortlist"] = json.loads(json.dumps([asdict(hit) for hit in ordered], default=str))
        return ordered, reason, assessment

    async def rank(self: TeiReranker, question: str, passages: list[str]) -> list[Scored]:
        if current["capture"]:
            return [Scored(index=i, score=1.0) for i in range(len(passages))]
        result = current["scores"][current["arm"]][current["id"]]["scores"]
        if len(result) != len(passages):
            raise ValueError("reranker response does not cover the actual candidate pool")
        return sorted(
            [Scored(index=i, score=s) for i, s in enumerate(result)],
            key=lambda s: (-s.score, s.index),
        )

    monkeypatch.setattr(TeiClient, "embed_query", embed)
    monkeypatch.setattr(retrieval.SearchService, "_rerank", rerank)
    monkeypatch.setattr(TeiReranker, "rank", rank)
    monkeypatch.setattr(retrieval, "RERANKER_BREAKER", Breaker())
    connector = procrastinate.PsycopgConnector(
        conninfo=owner_url.replace("postgresql+psycopg://", "postgresql://")
    )
    started = time.monotonic()
    if os.environ.get("ZENITH_E2E_CAPTURE_ONLY"):
        telemetry: dict[str, dict[str, Any]] = {}
        actual_persist = IngestionPipeline._persist  # pyright: ignore[reportPrivateUsage]
        actual_ingest = IngestionPipeline._ingest  # pyright: ignore[reportPrivateUsage]

        async def timed_persist(
            self: IngestionPipeline,
            document_id: UUID,
            pages: list[ParsedPage],
            chunks: list[Chunk],
            embeddings: list[list[float]],
        ) -> None:
            before = time.monotonic()
            item = telemetry.setdefault(str(document_id), {})
            item["chunks"] = len(chunks)
            item["persist_succeeded"] = False
            try:
                await actual_persist(self, document_id, pages, chunks, embeddings)
                item["persist_succeeded"] = True
            finally:
                item["persist_seconds"] = time.monotonic() - before
                save(output / "ingestion-telemetry.json", telemetry)

        async def timed_ingest(
            self: IngestionPipeline, document_id: UUID, path: Path, media_type: str
        ) -> Result:
            before = time.monotonic()
            try:
                result = await actual_ingest(self, document_id, path, media_type)
                telemetry.setdefault(str(document_id), {})["status"] = result.status
                return result
            finally:
                item = telemetry.setdefault(str(document_id), {})
                item["ingest_seconds"] = time.monotonic() - before
                item["finished_after_upload_start_seconds"] = time.monotonic() - started
                save(output / "ingestion-telemetry.json", telemetry)

        monkeypatch.setattr(IngestionPipeline, "_persist", timed_persist)
        monkeypatch.setattr(IngestionPipeline, "_ingest", timed_ingest)
    with tasks.app.replace_connector(connector):
        async with tasks.app.open_async():
            schema_exists = False
            if os.environ.get("ZENITH_E2E_PERSISTENT_DB"):
                engine = create_async_engine(owner_url)
                async with engine.connect() as connection:
                    schema_exists = bool(
                        await connection.scalar(
                            text("SELECT to_regclass('public.procrastinate_jobs') IS NOT NULL")
                        )
                    )
                await engine.dispose()
            if not schema_exists:
                await tasks.app.schema_manager.apply_schema_async()
            async with baseline_client(api) as client:
                login = await client.post(
                    "/auth/login", json={"email": account.admin_email, "password": PASSWORD}
                )
                assert login.status_code == 200
                auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
                identifiers: list[str] = []
                uploads: list[dict[str, Any]] = []
                record["upload"] = {
                    "documents": uploads,
                    "corpus_sha256": fixture["protocol"]["corpus_sha256"],
                }
                for document in fixture["documents"]:
                    corpus = document["text"].encode()
                    upload = await client.post(
                        "/documents",
                        headers=auth,
                        files={"file": (document["filename"], corpus, "text/plain")},
                        data={"labels": str(account.finance_label)},
                    )
                    assert upload.status_code in (200, 201), upload.text
                    document_id = upload.json()["document"]["id"]
                    identifiers.append(document_id)
                    uploads.append(
                        {
                            "document_id": document_id,
                            "filename": document["filename"],
                            "ack_seconds": time.monotonic() - started,
                            "bytes": len(corpus),
                            "http_status": upload.status_code,
                            "pending": upload.json()["document"]["status"],
                        }
                    )
                save(output / "progress.json", record)
                await asyncio.wait_for(
                    tasks.app.run_worker_async(
                        queues=["ingestion"],
                        concurrency=1,
                        wait=False,
                        install_signal_handlers=False,
                    ),
                    timeout=2400,
                )
                login = await client.post(
                    "/auth/login", json={"email": account.admin_email, "password": PASSWORD}
                )
                assert login.status_code == 200
                auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
                for document_id in identifiers:
                    status = await client.get(f"/documents/{document_id}", headers=auth)
                    assert status.status_code == 200 and status.json()["status"] == "ready", (
                        status.text
                    )
                record["upload"]["ready_seconds"] = time.monotonic() - started
                reader = await profile_for(account)
                async with tenant_session(reader.context) as session:
                    chunks = [
                        dict(row)
                        for row in (
                            await session.execute(
                                text(
                                    "SELECT c.id AS chunk_id, c.char_start, c.char_end, "
                                    "c.text, d.filename "
                                    "FROM chunks c JOIN documents d ON d.id=c.document_id "
                                    "WHERE c.document_id=ANY(CAST(:ids AS uuid[]))"
                                ),
                                {"ids": identifiers},
                            )
                        )
                        .mappings()
                        .all()
                    ]
                record["upload"]["chunks"] = len(chunks)
                first_upload = output / "upload-first.json"
                if first_upload.exists():
                    original_upload = json.loads(first_upload.read_text(encoding="utf-8"))
                    if {d["document_id"] for d in original_upload["documents"]} != set(identifiers):
                        raise ValueError("resumed uploads changed document identities")
                    record["resumed_upload"] = record["upload"]
                    record["upload"] = original_upload
                else:
                    save(first_upload, record["upload"])
                for case in fixture["cases"]:
                    current["id"] = case["id"]
                    params = {"q": case["question"], "limit": "8"}
                    if case.get("scope_filename"):
                        scoped = next(
                            d["document_id"]
                            for d in record["upload"]["documents"]
                            if d["filename"] == case["scope_filename"]
                        )
                        params["documents"] = scoped
                    response = await client.get("/search", params=params, headers=auth)
                    assert response.status_code == 200 and not response.json()["degraded"], (
                        response.text
                    )
                    case["candidates"] = captured[case["question"]]
                    case["embedding"] = vectors[case["question"]]
                    case["gold_chunk_ids"] = [
                        str(h["chunk_id"]) for h in chunks if spans_supported(h, case)
                    ]
                    if case["id"] in prior_cases:
                        old = prior_cases[case["id"]]
                        if set(case["gold_chunk_ids"]) != set(old["gold_chunk_ids"]):
                            raise ValueError("persistent gold-span chunk identities changed")
                        case["gold_chunk_ids"] = old["gold_chunk_ids"]
                    record["captured_queries"] = len(captured)
                    save(output / "progress.json", record)
                record["phase"] = "await_rerankers_and_generator"
                save(
                    output / "candidates.json",
                    {"protocol": fixture["protocol"], "cases": fixture["cases"]},
                )
                save(output / "progress.json", record)
                save(
                    output / "capture-ready.json",
                    {
                        "panel_sha256": hashlib.sha256(
                            (output / "candidates.json").read_bytes()
                        ).hexdigest(),
                        "validated_actual_queries": len(captured),
                    },
                )
                print(
                    "Public ingestion and actual retrieval completed; waiting for model stages.",
                    flush=True,
                )
                if os.environ.get("ZENITH_E2E_CAPTURE_ONLY"):
                    record["phase"] = "capture_complete"
                    save(output / "capture-results.json", record)
                    return
                deadline = time.monotonic() + 4 * 3600
                await await_file(output / "models-ready.json", deadline)
                scores = {}
                for arm in ("bge", "jev"):
                    path = output / f"{arm}-scores.json"
                    await await_file(path, deadline)
                    data = json.loads(path.read_text(encoding="utf-8"))
                    assert (
                        data["panel_sha256"]
                        == hashlib.sha256((output / "candidates.json").read_bytes()).hexdigest()
                    )
                    scores[arm] = data["queries"]
                current["scores"], current["capture"] = scores, False
                provider = LocalEvaluationProvider(
                    output / "completions.jsonl", fixture["protocol"]["generator"]
                )

                async def resolve(context: TenantContext) -> LocalEvaluationProvider:
                    return provider

                monkeypatch.setattr(generation, "provider_for", resolve)
                record["phase"] = "generated_answers"
                refresh_token = login.json()["refresh_token"]
                refreshed_at = 0.0
                for case in fixture["cases"]:
                    if case["split"] != "test":
                        continue
                    current["id"] = case["id"]
                    if time.monotonic() - refreshed_at >= 600:
                        renewed = await client.post(
                            "/auth/refresh", json={"refresh_token": refresh_token}
                        )
                        assert renewed.status_code == 200
                        pair = renewed.json()
                        auth = {"Authorization": f"Bearer {pair['access_token']}"}
                        refresh_token = pair["refresh_token"]
                        refreshed_at = time.monotonic()
                    item = {
                        "id": case["id"],
                        "article": case["article"],
                        "question": case["question"],
                    }
                    arms = (
                        ("bge", "jev")
                        if int(hashlib.sha256(case["id"].encode()).hexdigest(), 16) % 2
                        else ("jev", "bge")
                    )
                    for arm in arms:
                        current["arm"] = arm
                        before = time.monotonic()
                        answered = await client.post(
                            "/query",
                            json={"question": case["question"]},
                            headers=auth,
                            timeout=1000,
                        )
                        if answered.status_code == 429:
                            await asyncio.sleep(int(answered.headers.get("Retry-After", "60")))
                            answered = await client.post(
                                "/query",
                                json={"question": case["question"]},
                                headers=auth,
                                timeout=1000,
                            )
                        assert answered.status_code == 200, answered.text
                        body = answered.json()
                        assert not body["degraded"], body
                        shortlist = current["shortlist"]
                        item[arm] = measure(case, body, shortlist)
                        item[arm]["response"] = body
                        item[arm]["shortlist"] = shortlist
                        item[arm]["query_replay_wall_seconds"] = time.monotonic() - before
                        raw = provider.last if not body["abstained"] or body["model"] else {}
                        item[arm]["generation"] = raw
                        invalid = [
                            n
                            for match in MARKER.finditer(raw.get("text", ""))
                            for n in map(int, match.group(1).split(","))
                            if n not in range(1, len(shortlist) + 1)
                        ]
                        item[arm]["raw_fabricated_markers"] = len(invalid)
                        async with tenant_session(
                            replace(reader.context, user_id=reader.user_id)
                        ) as session:
                            stored = await session.scalar(
                                text("SELECT count(*) FROM query_citations WHERE query_id=:q"),
                                {"q": body["query_id"]},
                            )
                        assert stored == len(body["citations"])
                    record["cases"].append(item)
                    save(output / "generated-results.json", record)
                    print(json.dumps({"completed_test_pairs": len(record["cases"])}), flush=True)
                record["phase"] = "complete"
                record["elapsed_seconds"] = time.monotonic() - started
                save(output / "generated-results.json", record)
