"""Benchmark-only stage clocks; never imported by the product worker."""

import json
import os
import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from pathlib import Path

document: ContextVar[str] = ContextVar("measured_document", default="unknown")


def checkpoint(record: dict[str, object], output: Path) -> None:
    """Preserve partial measurements before a worker or external runner is stopped."""
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2), encoding="utf-8")
    os.replace(temporary, output)


def sync_stage[**P, T](
    name: str,
    work: Callable[P, T],
    records: list[dict[str, object]],
    save: Callable[[], None] | None = None,
) -> Callable[P, T]:
    def timed(*args: P.args, **kwargs: P.kwargs) -> T:
        started = time.perf_counter()
        try:
            return work(*args, **kwargs)
        finally:
            records.append(
                {
                    "document_id": document.get(),
                    "stage": name,
                    "seconds": time.perf_counter() - started,
                }
            )
            if save is not None:
                save()

    return timed


def async_stage[**P, T](
    name: str,
    work: Callable[P, Awaitable[T]],
    records: list[dict[str, object]],
    save: Callable[[], None] | None = None,
) -> Callable[P, Awaitable[T]]:
    async def timed(*args: P.args, **kwargs: P.kwargs) -> T:
        started = time.perf_counter()
        try:
            return await work(*args, **kwargs)
        finally:
            records.append(
                {
                    "document_id": document.get(),
                    "stage": name,
                    "seconds": time.perf_counter() - started,
                }
            )
            if save is not None:
                save()

    return timed
