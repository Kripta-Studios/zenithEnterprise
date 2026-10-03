"""Bounded readiness and identity checks for the owned local evaluation services."""

import json
import math
import time
import urllib.request


def ready(base, kind, seconds, emit):
    deadline = time.monotonic() + seconds
    started = time.monotonic()
    last_error = "not_checked"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(base + "/health", timeout=5):
                pass
            with urllib.request.urlopen(base + "/info", timeout=5) as response:
                info = json.load(response)
            if kind == "embed":
                path, payload = "/embed", {"inputs": ["Prueba local de preparación."]}
            else:
                path, payload = (
                    "/rerank",
                    {
                        "query": "¿Cuál es la capital de España?",
                        "texts": ["La capital de España es Madrid."],
                    },
                )
            request = urllib.request.Request(
                base + path,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=min(60, seconds)) as response:
                result = json.load(response)
            if kind == "embed":
                valid = (
                    len(result) == 1
                    and len(result[0]) == 1024
                    and all(math.isfinite(v) for v in result[0])
                )
            else:
                valid = (
                    len(result) == 1
                    and result[0]["index"] == 0
                    and math.isfinite(result[0]["score"])
                )
            if not valid:
                raise ValueError("neutral model request returned malformed output")
            return {"info": info, "ready_seconds": time.monotonic() - started}
        except (OSError, TimeoutError) as error:
            last_error = type(error).__name__
            emit(model=kind, waiting_seconds=round(time.monotonic() - started, 1), error=last_error)
            time.sleep(min(2, max(0, deadline - time.monotonic())))
    raise TimeoutError(f"{kind} readiness exceeded {seconds}s; last error {last_error}")
