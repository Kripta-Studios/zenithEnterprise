"""Export source-free metrics from a completed public local-gate run."""

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path

WEIGHTS_SHA256 = "d9e3e081faff1eefb84019509b2f5558fd74c1a05a2c7db22f74174fcedb5286"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(run, output):
    state = read(run / "orchestration.json")
    if state != {"stage": "complete", "paid_calls": 0}:
        raise ValueError("only a completed local-only run can be exported")
    results = read(run / "local-gate-results.json")
    panel = read(run / "candidates.json")
    scores = read(run / "bge-scores.json")
    capture = read(run / "capture-results.json")
    telemetry = read(run / "ingestion-telemetry.json")
    assert results["panel_sha256"] == digest(run / "candidates.json")
    assert results["scores_sha256"] == digest(run / "bge-scores.json")
    assert capture["captured_queries"] == 160 and capture["phase"] == "capture_complete"
    assert len(panel["cases"]) == len(scores["queries"]) == len(results["cases"]) == 160
    assert set(scores["queries"]) == {c["id"] for c in panel["cases"]}
    uploaded = capture["upload"]["documents"]
    assert len(uploaded) == len(telemetry) == 33
    assert all(t["status"] == "ready" and t["persist_succeeded"] for t in telemetry.values())
    documents = []
    for document in uploaded:
        timing = telemetry[document["document_id"]]
        documents.append({k: document[k] for k in ("filename", "bytes", "ack_seconds")})
        documents[-1].update(timing)
    monolith = next(d for d in documents if d["filename"] == "sqac-full.txt")
    assert monolith["bytes"] == 844643 and monolith["chunks"] == 938
    durations = sorted(q["seconds"] for q in scores["queries"].values())
    resources = {}
    for kind in ("embed", "rerank"):
        rows = [
            read_line
            for line in (run / f"{kind}-resources.jsonl").read_text(encoding="utf-8").splitlines()
            if (read_line := json.loads(line))
        ]
        gpu = [
            tuple(int(v.strip()) for v in r["gpu"]["output"].splitlines()[0].split(","))
            for r in rows
            if r.get("gpu", {}).get("exit") == 0
        ]
        resources[kind] = {
            "samples": len(rows),
            "minimum_free_host_ram_mib": min(r["host_free_mib"] for r in rows),
            "maximum_aggregate_gpu_used_mib": max(g[0] for g in gpu),
            "maximum_aggregate_gpu_utilization_percent": max(g[2] for g in gpu),
            "resource_abort": any("resource_abort" in r for r in rows),
        }
        if resources[kind]["resource_abort"]:
            raise ValueError("resource-aborted run cannot be exported as successful")
    checks = read(run / "gate-capture-docker-checks.json")
    assert checks["commands"][0]["exit"] == 0
    result = {
        "measured_date": "2026-10-03",
        "run_identity": read(run / "run-identity.json"),
        "actual_pipeline_check": checks,
        "admission": {k: v for k, v in results.items() if k != "cases"},
        "case_diagnostics": results["cases"],
        "ingestion": {
            "original_corpus_as_one_document": monolith,
            "all_33_documents_ready_seconds": capture["upload"]["ready_seconds"],
            "all_33_documents_chunks": capture["upload"]["chunks"],
            "all_33_documents_bytes": sum(d["bytes"] for d in uploaded),
            "all_33_documents_ready": True,
            "monolith_persistence_fraction": monolith["persist_seconds"]
            / monolith["ingest_seconds"],
            "measurement_limit": (
                "one shared-laptop run; serial upload before worker; no speedup claim"
            ),
        },
        "local_reranker_seconds": {
            "count": len(durations),
            "median": statistics.median(durations),
            "p95_nearest_rank": durations[151],
            "total": sum(durations),
            "limit": "includes 128 pools of 32 and 32 controls with 1-3 candidates",
        },
        "models": {
            "embedding": read(run / "embed-preflight.json"),
            "reranker": read(run / "rerank-preflight.json"),
            "reranker_hf_revision": "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
            "reranker_weights_sha256": WEIGHTS_SHA256,
            "new_generation_calls": 0,
            "new_jev_calls": 0,
        },
        "resources": resources,
        "artifact_hashes": {
            name: digest(run / name)
            for name in (
                "capture-results.json",
                "candidates.json",
                "bge-scores.json",
                "ingestion-telemetry.json",
                "local-gate-results.json",
                "embed-resources.jsonl",
                "rerank-resources.jsonl",
            )
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with output.with_suffix(".csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results["cases"][0]))
        writer.writeheader()
        writer.writerows(results["cases"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.run, args.output)
