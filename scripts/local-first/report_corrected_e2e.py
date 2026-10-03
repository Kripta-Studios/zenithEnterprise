"""Publish source-free aggregates from the completed corrected-gate public repeat."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    load = lambda name: json.loads((args.run / name).read_text(encoding="utf-8"))
    summary = load("e2e-summary.json")
    graded = load("independently-graded.json")
    checks = load("spanish-e2e-docker-checks.json")
    assert load("orchestration.json")["stage"] == "complete"
    assert graded["phase"] == "complete" and len(graded["cases"]) == 128
    assert all(row["exit"] == 0 for row in checks["commands"])
    primary = "entailed_grounded_reference_match"
    combinations = Counter((int(row["bge"][primary]), int(row["jev"][primary])) for row in graded["cases"])
    diagnostics = {}
    for arm in ("bge", "jev"):
        rows = [row[arm] for row in graded["cases"]]
        diagnostics[arm] = {
            "strict_successes": sum(int(row[primary]) for row in rows),
            "answered": sum(not row["response"]["abstained"] for row in rows),
            "reference_matches": sum(int(row["reference_match"]) for row in rows),
            "grounded_reference_matches": sum(int(row["grounded_reference_match"]) for row in rows),
            "grounded_but_failed_nli": sum(row["grounded_reference_match"] and not row[primary] for row in rows),
            "pre_generation_abstentions": sum(not row["generation"] for row in rows),
            "generation_calls": sum(bool(row["generation"]) for row in rows),
            "reused_identical_prompts": sum(bool(row["generation"].get("reused_identical_prompt")) for row in rows),
            "new_local_completions": sum(bool(row["generation"]) and not row["generation"].get("reused_identical_prompt", False) for row in rows),
            "independent_claim_checks": sum(len(row["independent_claim_checks"]) for row in rows),
        }
    exported = {
        **summary,
        "diagnostics": diagnostics,
        "paired_outcomes": {
            "both_success": combinations[(1, 1)], "bge_only_success": combinations[(1, 0)],
            "jev_only_success": combinations[(0, 1)], "both_fail": combinations[(0, 0)],
        },
        "code": {key: checks[key] for key in ("head", "tree", "archive_sha256", "runner_image")},
        "actual_checks": checks["commands"],
        "new_paid_calls": 0,
        "repeat_design": "same frozen public cohort; corrected shared gate; exact cached scoring inputs; not an unseen holdout or online latency test",
        "artifacts": {name: hashlib.sha256((args.run / name).read_bytes()).hexdigest() for name in (
            "candidates.json", "bge-scores.json", "jev-scores.json", "generated-results.json",
            "independently-graded.json", "e2e-summary.json", "spanish-e2e-docker-checks.json",
        )},
    }
    args.output.mkdir(parents=True, exist_ok=True)
    prefix = args.output / "corrected-bge-e2e-results-2026-10-03"
    prefix.with_suffix(".json").write_text(json.dumps(exported, indent=2) + "\n", encoding="utf-8")
    fields = ["id", "article", "bge_primary", "jev_primary", "bge_abstained", "jev_abstained", "bge_grounded", "jev_grounded", "bge_generation_reused", "jev_generation_reused"]
    with prefix.with_suffix(".csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in graded["cases"]:
            writer.writerow({
                "id": row["id"], "article": row["article"],
                "bge_primary": row["bge"][primary], "jev_primary": row["jev"][primary],
                "bge_abstained": row["bge"]["abstained"], "jev_abstained": row["jev"]["abstained"],
                "bge_grounded": row["bge"]["grounded_reference_match"], "jev_grounded": row["jev"]["grounded_reference_match"],
                "bge_generation_reused": row["bge"]["generation"].get("reused_identical_prompt", False),
                "jev_generation_reused": row["jev"]["generation"].get("reused_identical_prompt", False),
            })
    print(json.dumps({"diagnostics": diagnostics, "paired_outcomes": exported["paired_outcomes"]}))


if __name__ == "__main__":
    main()
