"""Export source-free aggregates only from completed paired public ingestion checks."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import median


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    hashes = {}

    def read(path):
        hashes[str(path.relative_to(args.run))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text(encoding="utf-8"))

    checks = read(args.run / "paired-docker-checks.json")
    assert checks["commands"] and all(row["exit"] == 0 for row in checks["commands"])
    trials = []
    for index in range(8):
        arm = "baseline" if index in (0, 3, 4, 7) else "candidate"
        directory = args.run / f"trial-{index}-{arm}"
        result = read(directory / "capture-results.json")
        values = read(directory / "ingestion-telemetry.json")
        assert len(values) == 1
        timing = next(iter(values.values()))
        integrity = read(directory / "vector-integrity.json")
        requests = timing.pop("embedding_requests")
        assert timing["status"] == "ready" and timing["persist_succeeded"]
        assert timing["chunks"] == 938 and result["upload"]["chunks"] == 938
        assert len(result["upload"]["documents"]) == 1
        assert result["upload"]["documents"][0]["http_status"] == 201
        assert all(row["status"] == 200 for row in requests)
        assert sum(row["items"] for row in requests) == 938
        assert integrity["stored_vectors_equal"] and integrity["sources_and_coordinates_equal"]
        for name in ("embedding-source-bindings.json", "embedding-vectors.npy"):
            path = directory / name
            hashes[str(path.relative_to(args.run))] = hashlib.sha256(path.read_bytes()).hexdigest()
        trials.append(
            {
                "trial": index,
                "arm": arm,
                "warmup": index < 2,
                "pair": index // 2,
                **timing,
                "vector_integrity": integrity,
                "requests": len(requests),
                "embedding_http_seconds": sum(row["seconds"] for row in requests),
                "server_total_seconds": sum(
                    int(row["timing_headers"]["x-total-time"]) for row in requests
                )
                / 1000,
                "tokens": sum(int(row["timing_headers"]["x-compute-tokens"]) for row in requests),
                "ready_observed_seconds": result["upload"]["ready_seconds"],
                "bytes": result["upload"]["documents"][0]["bytes"],
                "corpus_sha256": result["upload"]["corpus_sha256"],
                "non_persistence_seconds": timing["ingest_seconds"] - timing["persist_seconds"],
            }
        )
    assert len({row["tokens"] for row in trials}) == 1
    assert len({row["corpus_sha256"] for row in trials}) == 1
    metrics = (
        "embedding_seconds",
        "non_persistence_seconds",
        "ingest_seconds",
        "persist_seconds",
        "ready_observed_seconds",
    )
    summary = {}
    for arm in ("baseline", "candidate"):
        measured = [row for row in trials if row["arm"] == arm and not row["warmup"]]
        assert len(measured) == 3
        summary[arm] = {metric: median(row[metric] for row in measured) for metric in metrics}
    gains = {
        metric: {
            "speedup": summary["baseline"][metric] / summary["candidate"][metric],
            "reduction_percent": 100
            * (1 - summary["candidate"][metric] / summary["baseline"][metric]),
        }
        for metric in metrics
    }
    exported = {
        "checks": checks,
        "trials": trials,
        "summary": summary,
        "gains": gains,
        "scope": (
            "one warmup pair and three alternating fresh upload pairs; new tenant each trial; "
            "same bounded database; both model services resident; shared laptop; "
            "not production p95"
        ),
        "artifact_sha256": hashes,
        "additional_provider_calls": 0,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    prefix = args.output / "ingestion-phase-results-2026-10-03"
    prefix.with_suffix(".json").write_text(json.dumps(exported, indent=2) + "\n", encoding="utf-8")
    fields = ("trial", "arm", "warmup", "pair", "requests", "tokens", *metrics)
    with prefix.with_suffix(".csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in trials)
    print(json.dumps({"summary": summary, "gains": gains}, indent=2))


if __name__ == "__main__":
    main()
