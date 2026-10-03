"""Export completed public performance measurements without source text or credentials."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import median


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    bindings = {}

    def read(relative):
        path = args.evidence / relative
        bindings[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text(encoding="utf-8"))

    def completed(relative):
        result = read(relative)
        assert result["commands"] and all(row["exit"] == 0 for row in result["commands"])
        return result

    persistence = read("persistence/paired-values/persistence.json")
    checks = completed("persistence/paired-values/persist-paired-docker-checks.json")
    rows = [row for row in persistence["trials"] if row["pair"] > 0]
    assert len(rows) == 6 and persistence["chunks"] == 938
    stages = {}
    for arm in ("baseline", "candidate"):
        measured = [row for row in rows if row["arm"] == arm]
        stages[arm] = {
            "median_seconds": median(row["seconds"] for row in measured),
            "sql_stage_median_seconds": {
                stage: median(row["sql"][stage]["seconds"] for row in measured)
                for stage in ("insert_chunks", "insert_chunk_embeddings")
            },
        }
    stages["speedup"] = stages["baseline"]["median_seconds"] / stages["candidate"]["median_seconds"]
    stages["reduction_percent"] = 100 * (1 - 1 / stages["speedup"])
    upload = read("upload-ready-values/capture-results.json")["upload"]
    telemetry = read("upload-ready-values/ingestion-telemetry.json")
    assert len(telemetry) == 1 and len(upload["documents"]) == 1
    timing = next(iter(telemetry.values()))
    assert timing["persist_succeeded"] and timing["status"] == "ready"
    assert timing["chunks"] == upload["chunks"] == 938
    upload_checks = completed("upload-ready-values/upload-ready-docker-checks.json")
    embedding = read("upload-ready-values/embed-ready.json")
    mcp = read("mcp-benchmark/mcp-batch.json")
    mcp_checks = completed("mcp-benchmark/mcp-batch-docker-checks.json")
    assert len(mcp["trials"]) == 30 and mcp["sources"] == 8
    exported = {
        "persistence": {**persistence, "measured_summary": stages, "checks": checks},
        "fresh_upload": {
            "bytes": upload["documents"][0]["bytes"],
            "corpus_sha256": upload["corpus_sha256"],
            "http_status": upload["documents"][0]["http_status"],
            "ack_from_experiment_start_seconds": upload["documents"][0]["ack_seconds"],
            "ready_observed_seconds": upload["ready_seconds"],
            "timing": timing,
            "non_persistence_ingest_seconds": timing["ingest_seconds"] - timing["persist_seconds"],
            "embedding": embedding,
            "checks": upload_checks,
            "scope": "one fresh public upload; not paired against historical multi-file upload",
        },
        "mcp": {**mcp, "checks": mcp_checks},
        "artifact_sha256": bindings,
        "new_paid_calls": 0,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    prefix = args.output / "agent-performance-results-2026-10-03"
    prefix.with_suffix(".json").write_text(json.dumps(exported, indent=2) + "\n", encoding="utf-8")
    with prefix.with_suffix(".csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["benchmark", "pair", "arm", "seconds"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {"benchmark": "persistence", **{k: row[k] for k in ("pair", "arm", "seconds")}}
            )
        for row in mcp["trials"]:
            writer.writerow(
                {
                    "benchmark": "mcp",
                    "pair": row["trial"],
                    "arm": row["mode"],
                    "seconds": row["seconds"],
                }
            )
    print(json.dumps(stages, indent=2))


if __name__ == "__main__":
    main()
