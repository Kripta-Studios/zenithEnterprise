"""Reuse successful identical pairs; independently score every changed retrieval input."""

import argparse
import json
import math
from pathlib import Path

from spanish_e2e import digest, save


def identity(hit):
    return (hit["filename"], hit["char_start"], hit["char_end"], hit["text"])


def prepare(panel, source_panel, source_scores, plan_path, pending_path):
    fresh = json.loads(panel.read_text(encoding="utf-8"))
    prior = json.loads(source_panel.read_text(encoding="utf-8"))
    scores = json.loads(source_scores.read_text(encoding="utf-8"))
    if fresh["protocol"] != prior["protocol"] or scores["panel_sha256"] != digest(source_panel):
        raise ValueError("pair cache protocol or source score binding changed")
    previous = {c["id"]: c for c in prior["cases"]}
    if set(previous) != {c["id"] for c in fresh["cases"]}:
        raise ValueError("pair cache changed the question set")
    plan = {
        "panel_sha256": digest(panel),
        "source_panel_sha256": digest(source_panel),
        "source_scores_sha256": digest(source_scores),
        "queries": {},
    }
    pending = {
        **fresh,
        "cases": [],
        "scoring_scope": "only uncached exact public query/passage pairs",
    }
    excluded = {"candidates", "embedding", "gold_chunk_ids"}
    for case in fresh["cases"]:
        old = previous[case["id"]]
        if {k: v for k, v in case.items() if k not in excluded} != {
            k: v for k, v in old.items() if k not in excluded
        }:
            raise ValueError("pair cache changed a question or reference input")
        values = dict(
            zip(
                map(identity, old["candidates"]),
                scores["queries"][case["id"]]["scores"],
                strict=True,
            )
        )
        if len(values) != len(old["candidates"]) or any(
            not math.isfinite(v) or not 0 <= v <= 1 for v in values.values()
        ):
            raise ValueError("duplicate or invalid cached pair scores")
        cached = [values.get(identity(h)) for h in case["candidates"]]
        missing = [i for i, value in enumerate(cached) if value is None]
        plan["queries"][case["id"]] = {"cached": cached, "pending_indexes": missing}
        pending["cases"].append({**case, "candidates": [case["candidates"][i] for i in missing]})
    save(pending_path, pending)
    plan["pending_panel_sha256"] = digest(pending_path)
    save(plan_path, plan)
    return sum(len(row["pending_indexes"]) for row in plan["queries"].values())


def combine(panel, plan_path, pending_scores, output):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    scored = json.loads(pending_scores.read_text(encoding="utf-8"))
    if (
        digest(panel) != plan["panel_sha256"]
        or scored["panel_sha256"] != plan["pending_panel_sha256"]
    ):
        raise ValueError("pair completion belongs to another retrieval input")
    queries = {}
    for qid, row in plan["queries"].items():
        values = list(row["cached"])
        fresh = scored["queries"][qid]["scores"]
        if len(fresh) != len(row["pending_indexes"]):
            raise ValueError("provider omitted an uncached pair")
        for index, value in zip(row["pending_indexes"], fresh, strict=True):
            values[index] = value
        if any(v is None or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
            raise ValueError("pair completion contains an invalid score")
        queries[qid] = {"scores": values}
    save(
        output,
        {
            **scored,
            "panel_sha256": plan["panel_sha256"],
            "queries": queries,
            "verified_pair_cache": {
                **plan,
                "queries": {
                    qid: {
                        "reused_pairs": len(row["cached"]) - len(row["pending_indexes"]),
                        "fresh_pairs": len(row["pending_indexes"]),
                    }
                    for qid, row in plan["queries"].items()
                },
                "pending_scores_sha256": digest(pending_scores),
                "latency_scope": "cached pair responses; not online full-query rerank latency",
            },
        },
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "combine"])
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--source-panel", type=Path)
    parser.add_argument("--source-scores", type=Path)
    parser.add_argument("--pending-panel", type=Path)
    parser.add_argument("--pending-scores", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        if not all((args.source_panel, args.source_scores, args.pending_panel)):
            parser.error("prepare requires source panel/scores and a pending-panel destination")
        print(
            json.dumps(
                {
                    "uncached_pairs": prepare(
                        args.panel,
                        args.source_panel,
                        args.source_scores,
                        args.plan,
                        args.pending_panel,
                    )
                }
            )
        )
    else:
        if not all((args.pending_scores, args.output)):
            parser.error("combine requires pending scores and output")
        combine(args.panel, args.plan, args.pending_scores, args.output)


if __name__ == "__main__":
    main()
