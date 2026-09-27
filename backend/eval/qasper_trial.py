"""Frozen, human-annotated QASPER evidence benchmark for the isolated R1 index.

Download the official v0.3 train/dev archive as documented in the R1 report.
Only the development split is read. No source corpus or vectors enter Git.
"""

import argparse
import hashlib
import json
import random
import statistics
import time
from pathlib import Path
from typing import cast
from uuid import NAMESPACE_URL, uuid5

from app.features.ingestion.chunking.lossless import Source, atomic_spans, structural_groups
from eval.embedder import TeiEmbedder
from eval.evidence_common import (
    EMBED_MODEL,
    RENDER_BUDGET_TOKENS,
    TOP_K,
    TrialUnit,
    rank,
    rendered_token_counts,
)
from eval.qasper_common import (
    Case,
    Paper,
    build_paper,
    legacy_units_for_paper,
    load_papers,
    score_case,
)

__all__ = ["Case", "Paper", "build_paper", "load_papers", "score_case", "units_for_paper"]

ARCHIVE_SHA256 = "a28fdf966db827bcee3d873107d6b6669864fb7ca8fbf73a192f5e39191bdb5a"
DEV_SHA256 = "2ae7ee62a65b1c4225791c70de80c2aad4e8998cf1fd4f09a53103db4f21af93"
DATASET_URL = "https://qasper-dataset.s3.us-west-2.amazonaws.com/qasper-train-dev-v0.3.tgz"
TRIAL_VERSION = "zenith-r1-qasper-dev-64-v1"
DOCUMENT_COUNT = 64
BOOTSTRAP_SEED = 1729
BOOTSTRAP_SAMPLES = 2000


def units_for_paper(
    paper: Paper, *, source_version: str = "qasper-v0.3"
) -> tuple[list[TrialUnit], list[TrialUnit]]:
    legacy = legacy_units_for_paper(paper)
    source = Source(
        uuid5(NAMESPACE_URL, f"{source_version}:{paper.id}"),
        None,
        paper.text,
        hashlib.sha256(paper.text.encode()).hexdigest(),
        f"{source_version}-render-v1",
        source_version,
    )
    groups = [
        TrialUnit(f"group:{item.id}", item.start, item.end, item.text)
        for item in structural_groups(
            source, atomic_spans(source, max_chars=1000), target_chars=1200, max_chars=1600
        )
    ]
    if not legacy or not groups:
        raise ValueError("selected paper has no retrievable units")
    return legacy, groups


def summarize(rows: list[dict[str, object]]) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for route in ("legacy", "grouped_from_legacy", "resegmented_reembedded"):
        scores = [
            cast(dict[str, dict[str, float | bool | int]], row["routes"])[route] for row in rows
        ]
        result[route] = {
            "cases": len(scores),
            "complete_evidence_rate": statistics.mean(
                float(score["complete_evidence"]) for score in scores
            ),
            "mean_evidence_recall": statistics.mean(
                float(score["evidence_recall"]) for score in scores
            ),
            "top1_intersects_evidence_rate": statistics.mean(
                float(score["top1_intersects_evidence"]) for score in scores
            ),
            "mean_rendered_tokens": statistics.mean(
                float(score["rendered_tokens"]) for score in scores
            ),
        }
    return result


def paired_paper_bootstrap(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Prespecified document-cluster bootstrap of paired completeness differences."""
    paper_scores: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        paper_id = cast(str, row["paper_id"])
        routes = cast(dict[str, dict[str, float | bool | int]], row["routes"])
        per_paper = paper_scores.setdefault(paper_id, {})
        for route, score in routes.items():
            per_paper.setdefault(route, []).append(float(score["complete_evidence"]))
    paper_ids = sorted(paper_scores)
    result: dict[str, dict[str, object]] = {}
    rng = random.Random(BOOTSTRAP_SEED)
    for route in ("grouped_from_legacy", "resegmented_reembedded"):
        differences = [
            statistics.mean(paper_scores[paper_id][route])
            - statistics.mean(paper_scores[paper_id]["legacy"])
            for paper_id in paper_ids
        ]
        replicates = sorted(
            statistics.mean(rng.choice(differences) for _ in differences)
            for _ in range(BOOTSTRAP_SAMPLES)
        )
        result[route] = {
            "macro_paper_difference": statistics.mean(differences),
            "percentile_95_interval": [replicates[49], replicates[1949]],
            "paper_clusters": len(paper_ids),
        }
    return result


def evaluate_papers(
    papers: tuple[Paper, ...], *, tei_url: str, source_version: str
) -> dict[str, object]:
    embedder = TeiEmbedder(tei_url)
    rows: list[dict[str, object]] = []
    timings: dict[str, float] = {"tokenization": 0, "legacy_embedding": 0, "group_embedding": 0}
    segment_counts: dict[str, int] = {"legacy": 0, "structural": 0}
    for paper_number, paper in enumerate(papers, 1):
        legacy, groups = units_for_paper(paper, source_version=source_version)
        segment_counts["legacy"] += len(legacy)
        segment_counts["structural"] += len(groups)
        started = time.perf_counter()
        token_counts = rendered_token_counts(legacy + groups, tei_url)
        timings["tokenization"] += time.perf_counter() - started
        started = time.perf_counter()
        legacy_vectors = embedder.encode([unit.text for unit in legacy], batch=4)
        timings["legacy_embedding"] += time.perf_counter() - started
        started = time.perf_counter()
        group_vectors = embedder.encode([unit.text for unit in groups], batch=4)
        timings["group_embedding"] += time.perf_counter() - started
        query_vectors = embedder.encode([case.question for case in paper.cases], batch=4)
        for case, query_vector in zip(paper.cases, query_vectors, strict=True):
            legacy_ranked = rank(legacy, legacy_vectors, query_vector)
            group_ranked = rank(groups, group_vectors, query_vector)
            leaders = {unit.id: position for position, unit in enumerate(legacy_ranked)}
            grouped = sorted(
                groups,
                key=lambda group: (
                    min(
                        (
                            leaders[unit.id]
                            for unit in legacy
                            if unit.start < group.end and unit.end > group.start
                        ),
                        default=len(legacy),
                    ),
                    group.start,
                ),
            )
            rows.append(
                {
                    "paper_id": paper.id,
                    "question_id": case.id,
                    "label_choice": case.label_choice,
                    "evidence_options": len(case.evidence_options),
                    "minimum_gold_passages": min(len(x) for x in case.evidence_options),
                    "routes": {
                        "legacy": score_case(case, legacy_ranked, token_counts),
                        "grouped_from_legacy": score_case(case, grouped, token_counts),
                        "resegmented_reembedded": score_case(case, group_ranked, token_counts),
                    },
                }
            )
        print(f"  evaluated paper {paper_number}/{len(papers)}", flush=True)
    if not rows:
        raise ValueError("frozen benchmark yielded no mappable evidence")
    return {
        "source_version": source_version,
        "source_ids": [paper.id for paper in papers],
        "all_questions_in_selected_papers": sum(paper.questions for paper in papers),
        "eligible_questions": len(rows),
        "embedding_model": EMBED_MODEL,
        "embedding_endpoint": tei_url,
        "tokenizer": EMBED_MODEL,
        "top_k": TOP_K,
        "render_budget_tokens": RENDER_BUDGET_TOKENS,
        "segment_counts": segment_counts,
        "one_time_seconds": {key: round(value, 3) for key, value in timings.items()},
        "summary": summarize(rows),
        "paired_paper_bootstrap": {
            "seed": BOOTSTRAP_SEED,
            "samples": BOOTSTRAP_SAMPLES,
            "metric": "complete evidence rate, equal paper weight, route minus legacy",
            "routes": paired_paper_bootstrap(rows),
        },
        "cases": rows,
    }


def run(path: Path, *, tei_url: str) -> dict[str, object]:
    papers = load_papers(path)
    return {
        "trial_version": TRIAL_VERSION,
        "dataset_url": DATASET_URL,
        "archive_sha256": ARCHIVE_SHA256,
        "dev_sha256": DEV_SHA256,
        "selection": "64 document IDs with smallest SHA256(ID) on QASPER v0.3 dev",
        "label_provenance": (
            "QASPER practitioner answer-evidence annotations; exact unique paragraphs only"
        ),
        **evaluate_papers(papers, tei_url=tei_url, source_version="qasper-v0.3"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev-json", type=Path, required=True)
    parser.add_argument("--tei-url", default="http://127.0.0.1:18081")
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    report = run(options.dev_json, tei_url=options.tei_url)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {options.output}")


if __name__ == "__main__":
    main()
