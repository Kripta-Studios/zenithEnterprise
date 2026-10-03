"""Bounded readiness and identity checks for the owned local evaluation services."""

import json
import math
import time
import urllib.request


def completed_scores(panel_path, output):
    """A completed stage can resume only against its exact ordered capture."""
    import hashlib

    panel = json.loads(panel_path.read_text(encoding="utf-8"))
    panel_hash = hashlib.sha256(panel_path.read_bytes()).hexdigest()
    expected = {case["id"]: len(case["candidates"]) for case in panel["cases"]}
    for arm in ("bge", "jev"):
        path = output / f"{arm}-scores.json"
        if not path.exists():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["panel_sha256"] != panel_hash or set(data["queries"]) != set(expected):
            raise ValueError("completed scores do not match the resumed capture")
        for qid, length in expected.items():
            values = data["queries"][qid]["scores"]
            if len(values) != length or any(
                isinstance(v, bool) or not math.isfinite(v) or not 0 <= v <= 1 for v in values
            ):
                raise ValueError("completed scores are incomplete or malformed")
    return True


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
