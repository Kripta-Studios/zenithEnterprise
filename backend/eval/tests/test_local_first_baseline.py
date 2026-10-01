"""Opt-in measurements using real REST routes, queue, app-role DB and existing TEI clients.

This is a disposable public-fixture benchmark, not a quality assertion or a network SLA.
If model services are not healthy, record upload-to-pending and the unmet prerequisite.
"""

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import procrastinate
import pytest
from fastapi import FastAPI
from sqlalchemy import text

from app.common.exceptions import ZenithError
from app.core.config import settings
from app.core.database import owner_session
from app.features.auth.router import router as auth_router
from app.features.documents.router import router as documents_router
from app.features.ingestion import tasks
from app.features.retrieval.router import router as retrieval_router
from app.main import handle_domain_error
from conftest import PASSWORD, Account

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not os.environ.get("ZENITH_RUN_LOCAL_BASELINE"), reason="opt-in real-model local baseline"
    ),
]


async def test_public_upload_baseline(
    account: Account,
    owner_url: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = Path(os.environ["ZENITH_BASELINE_SQAC"])
    output = Path(os.environ["ZENITH_BASELINE_OUTPUT"])
    payload = json.loads(source.read_text(encoding="utf-8"))
    paragraphs = [p["context"] for item in payload["data"] for p in item["paragraphs"]]
    fixtures = [
        ("small.txt", "\n\n".join(paragraphs[:3]).encode(), "text/plain"),
        ("medium.txt", "\n\n".join(paragraphs[:100]).encode(), "text/plain"),
    ]
    # Reuse the existing PDF fixture writer, with stable timestamps and IDs for measurement.
    from reportlab import rl_config

    from app.features.ingestion.tests.test_pipeline import pdf_bytes

    monkeypatch.setattr(rl_config, "invariant", 1)

    fixtures.append(
        ("public-qa.pdf", pdf_bytes([p[:1800] for p in paragraphs[:10]]), "application/pdf")
    )
    api = FastAPI()
    api.add_exception_handler(ZenithError, handle_domain_error)  # type: ignore[arg-type]
    for router in (auth_router, documents_router, retrieval_router):
        api.include_router(router)
    record: dict[str, Any] = {
        "fixture_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "transport": "in-process ASGI multipart; excludes network transfer",
        "worker_concurrency": 1,
        "uploads": [],
        "phase_events": [],
        "upload_to_ready": None,
        "queries_idle": [],
        "queries_ingesting": [],
    }
    events = record["phase_events"]
    beginning = time.monotonic()
    from app.features.ingestion.pipeline import IngestionPipeline

    # External benchmark instrumentation; product code is unchanged.
    original_status = IngestionPipeline._set_status  # pyright: ignore[reportPrivateUsage]

    async def status(self: IngestionPipeline, document_id: UUID, value: str) -> None:
        await original_status(self, document_id, value)
        events.append(
            {
                "document_id": str(document_id),
                "status": value,
                "seconds": round(time.monotonic() - beginning, 6),
            }
        )

    monkeypatch.setattr(IngestionPipeline, "_set_status", status)
    monkeypatch.setattr(
        settings, "tei_embed_url", os.environ.get("ZENITH_BASELINE_EMBED", "http://127.0.0.1:18081")
    )
    monkeypatch.setattr(
        settings,
        "tei_rerank_url",
        os.environ.get("ZENITH_BASELINE_RERANK", "http://127.0.0.1:18082"),
    )
    monkeypatch.setattr(settings, "hardware", "cpu")
    monkeypatch.delenv("ZENITH_DISABLE_INGESTION_QUEUE", raising=False)
    connector = procrastinate.PsycopgConnector(
        conninfo=owner_url.replace("postgresql+psycopg://", "postgresql://")
    )
    with tasks.app.replace_connector(connector):
        async with tasks.app.open_async():
            await tasks.app.schema_manager.apply_schema_async()
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=api), base_url="http://fixture"
            ) as client:
                login = await client.post(
                    "/auth/login", json={"email": account.admin_email, "password": PASSWORD}
                )
                assert login.status_code == 200
                auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
                model_health: dict[str, bool | str] = {}
                async with httpx.AsyncClient(timeout=2) as health:
                    for name, url in [
                        ("embed", settings.tei_embed_url),
                        ("rerank", settings.tei_rerank_url),
                    ]:
                        try:
                            response = await health.get(f"{url}/health")
                            model_health[name] = response.status_code == 200
                        except httpx.HTTPError as exc:
                            model_health[name] = type(exc).__name__
                record["model_health"] = model_health
                ids: list[str] = []
                for filename, content, media in fixtures:
                    path = tmp_path / filename
                    path.write_bytes(content)
                    started = time.monotonic()
                    with path.open("rb") as stream:
                        response = await client.post(
                            "/documents",
                            files={"file": (filename, stream, media)},
                            data={"labels": str(account.finance_label)},
                            headers=auth,
                        )
                    assert response.status_code == 201, response.text
                    body = response.json()
                    ids.append(str(body["document"]["id"]))
                    item: dict[str, Any] = {
                        "filename": filename,
                        "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "document_id": ids[-1],
                        "upload_start_seconds": round(started - beginning, 6),
                        "ack_seconds": round(time.monotonic() - started, 6),
                        "http_status": response.status_code,
                        "document_status_at_ack": body["document"]["status"],
                    }
                    started = time.monotonic()
                    duplicate = await client.post(
                        "/documents",
                        files={"file": (filename, content, media)},
                        data={"labels": str(account.finance_label)},
                        headers=auth,
                    )
                    assert duplicate.status_code == 200 and duplicate.json()["deduplicated"]
                    item["duplicate_ack_seconds"] = round(time.monotonic() - started, 6)
                    item["duplicate_http_status"] = duplicate.status_code
                    record["uploads"].append(item)
                # Owner credentials inspect queue infrastructure only.
                # Customer content uses authenticated REST and the application role with RLS.
                async with owner_session() as session:
                    jobs = await session.scalar(
                        text(
                            "SELECT count(*) FROM procrastinate_jobs "
                            "WHERE task_name='ingest_document'"
                        )
                    )
                record["queued_jobs"] = jobs
                assert jobs == len(fixtures), "duplicates must not enqueue more ingestion work"
                if all(value is True for value in model_health.values()):
                    started = time.monotonic()
                    try:
                        await asyncio.wait_for(
                            tasks.app.run_worker_async(
                                queues=["ingestion"],
                                concurrency=1,
                                wait=False,
                                install_signal_handlers=False,
                            ),
                            timeout=300,
                        )
                        record["queue_drain_seconds"] = round(time.monotonic() - started, 6)
                        statuses = [
                            (await client.get(f"/documents/{identifier}", headers=auth)).json()[
                                "status"
                            ]
                            for identifier in ids
                        ]
                        record["final_statuses"] = statuses
                        record["upload_to_ready"] = (
                            [
                                {
                                    "document_id": item["document_id"],
                                    "seconds": round(
                                        next(
                                            event["seconds"]
                                            for event in events
                                            if event["document_id"] == item["document_id"]
                                            and event["status"] == "ready"
                                        )
                                        - item["upload_start_seconds"],
                                        6,
                                    ),
                                }
                                for item in record["uploads"]
                            ]
                            if all(s == "ready" for s in statuses)
                            else None
                        )
                    except TimeoutError:
                        record["blocked"] = "worker did not drain within 300 seconds"
                else:
                    record["blocked"] = (
                        "model readiness: worker and query timings were not executed"
                    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record))
