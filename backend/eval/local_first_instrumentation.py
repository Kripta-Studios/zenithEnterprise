"""Benchmark-only stage clocks; never imported by the product worker."""

import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

document: ContextVar[str] = ContextVar("measured_document", default="unknown")


def sync_stage[**P, T](
    name: str, work: Callable[P, T], records: list[dict[str, object]]
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

    return timed


def async_stage[**P, T](
    name: str, work: Callable[P, Awaitable[T]], records: list[dict[str, object]]
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

    return timed
