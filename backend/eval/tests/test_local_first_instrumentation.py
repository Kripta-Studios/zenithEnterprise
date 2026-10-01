"""Measurement evidence survives failed or cancelled pipeline stages."""

import asyncio
import json
from pathlib import Path

import pytest

from eval.local_first_instrumentation import async_stage, checkpoint, document, sync_stage


def test_failed_stage_checkpoints_partial_record(tmp_path: Path) -> None:
    output = tmp_path / "partial.json"
    events: list[dict[str, object]] = []
    record: dict[str, object] = {"stages": events, "upload_to_ready": None}
    checkpoint(record, output)

    def fail() -> None:
        raise RuntimeError("model failed")

    token = document.set("public-fixture-id")
    try:
        with pytest.raises(RuntimeError, match="model failed"):
            sync_stage("embed", fail, events, lambda: checkpoint(record, output))()
    finally:
        document.reset(token)
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["upload_to_ready"] is None
    assert saved["stages"][0]["document_id"] == "public-fixture-id"
    assert saved["stages"][0]["stage"] == "embed"
    assert not output.with_suffix(".json.tmp").exists()


async def test_cancelled_stage_is_saved_and_cancellation_propagates(tmp_path: Path) -> None:
    output = tmp_path / "cancelled.json"
    events: list[dict[str, object]] = []
    started = asyncio.Event()

    async def waiting() -> None:
        started.set()
        await asyncio.Event().wait()

    work = async_stage(
        "send_batch", waiting, events, lambda: checkpoint({"stages": events}, output)
    )
    task = asyncio.ensure_future(work())
    await asyncio.wait_for(started.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert json.loads(output.read_text(encoding="utf-8"))["stages"][0]["stage"] == "send_batch"
