"""Export completed paired evidence without questions, source text or completions."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def export(run: Path, output: Path) -> None:
    generated = read(run / "generated-results.json")
    graded = read(run / "independently-graded.json")
    summary = read(run / "e2e-summary.json")
    panel = read(run / "candidates.json")
    checks = read(run / "spanish-e2e-docker-checks.json")
    orchestration = read(run / "orchestration.json")
    cases = {c["id"]: c for c in panel["cases"] if c["split"] == "test"}
    raw = {r["id"]: r for r in generated["cases"]}
    rows = graded["cases"]
    digest = hashlib.sha256((run / "generated-results.json").read_bytes()).hexdigest()
    if (
        generated["phase"] != "complete"
        or len(rows) != 128
        or len({r["id"] for r in rows}) != 128
        or set(raw) != set(cases)
        or {r["id"] for r in rows} != set(cases)
        or graded["independent_nli"]["input_sha256"] != digest
        or summary["test_pairs"] != 128
        or graded["fixture_sha256"] != generated["fixture_sha256"]
        or orchestration["stage"] != "complete"
        or orchestration["summary_sha256"]
        != hashlib.sha256((run / "e2e-summary.json").read_bytes()).hexdigest()
        or any(c["exit"] != 0 for c in checks["commands"])
    ):
        raise ValueError("completed, independently graded integration evidence required")
    counts = {arm: Counter() for arm in ("bge", "jev")}
    pairs = Counter()
    exported = []
    query_ids = set()
    for row in rows:
        case = cases[row["id"]]
        flat = {"case_id": row["id"], "article_id": row["article"]}
        for arm in ("bge", "jev"):
            item = row[arm]
            response = item["response"]
            if (
                "independent_claim_checks" not in item
                or response != raw[row["id"]][arm]["response"]
                or item["shortlist"] != raw[row["id"]][arm]["shortlist"]
                or response["degraded"]
                or response["query_id"] in query_ids
            ):
                raise ValueError("invalid or changed generated response evidence")
            query_ids.add(response["query_id"])
            shortlist = item["shortlist"]
            lexical = sum(h["lexical_rank"] is not None for h in shortlist)
            veto = bool(shortlist) and lexical / len(shortlist) < 1 / 3
            top = max((h["rerank_score"] for h in shortlist), default=0)
            gold = any(h["chunk_id"] in case["gold_chunk_ids"] for h in shortlist)
            called = bool(item["generation"])
            metrics = {
                "candidate_gold_hit32": any(
                    h["chunk_id"] in case["gold_chunk_ids"] for h in case["candidates"]
                ),
                "shortlist_gold_hit8": gold,
                "lexical_hits8": lexical,
                "lexical_veto": veto,
                "lexical_veto_with_gold8": veto and gold,
                "score_floor_veto": top < 0.02,
                "score_floor_only_veto": top < 0.02 and not veto,
                "generation_called": called,
                "pre_generation_abstained": bool(item["abstained"]) and not called,
                "post_generation_abstained": bool(item["abstained"]) and called,
                "answered": not bool(item["abstained"]),
                "english_canned_abstention": response["answer"]
                == "The documents provided do not contain an answer to this question.",
                "primary": item["entailed_grounded_reference_match"],
                "reference_and_citation_match": item["grounded_reference_match"],
                "reference_match": item["reference_match"],
                "citation_count": item["citation_count"],
                "invalid_citations": item["invalid_citations"],
                "raw_fabricated_markers": item["raw_fabricated_markers"],
                "all_sentences_entailed": bool(item["independent_claim_checks"])
                and item["nli_minimum_entailment"] >= 0.8,
                "checked_claims": len(item["independent_claim_checks"]),
            }
            counts[arm].update({k: int(v) for k, v in metrics.items()})
            flat.update({f"{arm}_{k}": v for k, v in metrics.items()})
        bge = bool(flat["bge_primary"])
        jev = bool(flat["jev_primary"])
        category = (
            "both_pass"
            if bge and jev
            else "both_fail"
            if not bge and not jev
            else ("jev_only_pass" if jev else "bge_only_pass")
        )
        flat["paired_primary_outcome"] = category
        pairs[category] += 1
        if category == "jev_only_pass":
            pairs["jev_only_pass_bge_pre_generation_abstained"] += int(
                flat["bge_pre_generation_abstained"]
            )
            pairs["jev_only_pass_both_generated"] += int(
                flat["bge_generation_called"] and flat["jev_generation_called"]
            )
        if flat["bge_generation_called"] and flat["jev_generation_called"]:
            pairs["both_generated"] += 1
            pairs["both_generated_bge_primary"] += int(bge)
            pairs["both_generated_jev_primary"] += int(jev)
        exported.append(flat)
    for arm in ("bge", "jev"):
        if counts[arm]["primary"] / 128 != summary[arm]["entailed_grounded_reference_match"]:
            raise ValueError("primary summary differs from independently graded case counts")
    public = {k: v for k, v in summary.items() if k != "upload"}
    public["upload"] = {
        "documents": len(graded["upload"]["documents"]),
        "uploaded_bytes": sum(d["bytes"] for d in graded["upload"]["documents"]),
        "chunks": graded["upload"]["chunks"],
        "ready_seconds": graded["upload"]["ready_seconds"],
        "corpus_sha256": graded["upload"]["corpus_sha256"],
    }
    public["diagnostic_counts"] = counts
    public["paired_primary_counts"] = pairs
    public["article_clusters"] = len({r["article"] for r in rows})
    public["independent_nli"] = graded["independent_nli"]
    public["integration_check"] = checks
    residency = read(run / "generator-preflight.json")["residency"]["models"]
    generator = next(
        m for m in residency if m["digest"] == graded["protocol"]["generator"]["model_digest"]
    )
    resources = [
        json.loads(line)
        for line in (run / "generation-resources.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    public["execution_readiness"] = {
        "embedder_warm_ready_seconds": read(run / "embed-preflight.json")["ready_seconds"],
        "reranker_ready_seconds": read(run / "bge-preflight.json")["ready_seconds"],
        "generator_resident_bytes": generator["size"],
        "generator_vram_bytes": generator["size_vram"],
        "generator_context_length": generator["context_length"],
        "generation_resource_samples": len(resources),
        "minimum_generation_free_host_mib": min(r["host_free_mib"] for r in resources),
    }
    public["input_sha256"] = {
        name: hashlib.sha256((run / name).read_bytes()).hexdigest()
        for name in (
            "generated-results.json",
            "independently-graded.json",
            "candidates.json",
            "bge-scores.json",
            "jev-scores.json",
            "e2e-summary.json",
            "generator-preflight.json",
            "embed-preflight.json",
            "bge-preflight.json",
            "generation-resources.jsonl",
        )
    }
    public["diagnostic_limits"] = [
        "gate counts reproduce frozen lexical share <1/3 and top-score floor <0.02",
        "veto-with-gold is an admission diagnostic, not a counterfactual generated success",
        "both-generated subset is post-treatment selection, not a causal provider estimate",
        "English canned abstentions are preserved; generated answers were not translated",
    ]
    output.mkdir(parents=True, exist_ok=True)
    (output / "spanish-e2e-results-2026-10-03.json").write_text(
        json.dumps(public, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    with (output / "spanish-e2e-cases-2026-10-03.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(exported[0]))
        writer.writeheader()
        writer.writerows(exported)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.run, args.output)
