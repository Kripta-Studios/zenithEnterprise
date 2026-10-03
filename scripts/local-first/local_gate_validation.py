"""Freeze fresh published questions and compare two admission rules on real local scores."""

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from eval.spanish_e2e import contexts, save, sha  # noqa: E402

SEED = 20261003


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare(old_path, sqac_path, negative_path, output):
    old = read(old_path)
    used_articles = {c["article"] for c in old["cases"]}
    fresh = sorted(
        [c for c in contexts(sqac_path) if sha(c["title"]) not in used_articles],
        key=lambda c: sha(f"{SEED}|{c['key']}"),
    )
    chosen = []
    families = set()
    for context in fresh:
        if context["title"] not in families:
            chosen.append(context)
            families.add(context["title"])
        if len(chosen) == 128:
            break
    if len(chosen) != 128:
        raise ValueError("128 unused article families required")
    corpus = old["corpus"]
    documents = [{"filename": "sqac-full.txt", "text": corpus}]
    cases = []
    for context in chosen:
        question = min(context["questions"], key=lambda q: sha(f"{SEED}|{q['id']}"))
        begin = corpus.index(context["text"])
        cases.append(
            {
                "id": question["id"],
                "question": question["question"],
                "split": "test",
                "article": sha(context["title"]),
                "context_key": context["key"],
                "filename": "sqac-full.txt",
                "answers": [
                    {**a, "start": a["start"] + begin, "end": a["end"] + begin}
                    for a in question["answers"]
                ],
            }
        )
    negatives = []
    for article in read(negative_path)["data"]:
        for paragraph in article["paragraphs"]:
            for question in paragraph["qas"]:
                if question.get("is_impossible") and not question["answers"]:
                    negatives.append((article["title"], paragraph["context"], question))
    negatives.sort(key=lambda item: sha(f"{SEED}|{item[2]['id']}"))
    selected_families = set()
    for title, context, question in negatives:
        if title in selected_families:
            continue
        selected_families.add(title)
        filename = f"unanswerable-{len(selected_families):03d}.txt"
        documents.append({"filename": filename, "text": context})
        cases.append(
            {
                "id": question["id"],
                "question": question["question"],
                "split": "negative",
                "article": sha(title),
                "context_key": sha(context),
                "filename": filename,
                "scope_filename": filename,
                "answers": [],
            }
        )
        if len(selected_families) == 32:
            break
    if len(selected_families) != 32 or len({c["question"] for c in cases}) != len(cases):
        raise ValueError("complete unique unanswerable control cohort required")
    protocol = {
        "seed": SEED,
        "test_cases": 128,
        "negative_cases": 32,
        "development_cases": 0,
        "corpus_sha256": sha(corpus),
        "corpus_bytes": len(corpus.encode()),
        "document_count": len(documents),
        "retrieved_candidates": 32,
        "generated_passages": 8,
        "batch_tokens": 1024,
        "batch_items": 2,
        "experiment": "local reranking and admission, no generated-answer accuracy claim",
        "old_fixture_sha256": hashlib.sha256(old_path.read_bytes()).hexdigest(),
        "sqac_sha256": hashlib.sha256(sqac_path.read_bytes()).hexdigest(),
        "negative_sha256": hashlib.sha256(negative_path.read_bytes()).hexdigest(),
        "selection": "one fresh SQAC question per previously unused article family",
        "negative_scope": "published impossible question restricted to its own source document",
        "negative_limits": "automatically translated SQuAD v2; not human Spanish adjudication",
        "positive_labels": "published SQAC human answer spans",
        "policies": {
            "old": "lexical share in selected eight",
            "new": "lexical share in hydrated candidates",
        },
        "lexical_share_floor": 1 / 3,
        "rerank_floor": 0.02,
        "acceptance": {
            "gold_admission_gain_at_least": 0.05,
            "negative_admission_increase_at_most": 0,
        },
        "paid_provider_calls": 0,
    }
    save(output, {"protocol": protocol, "corpus": corpus, "documents": documents, "cases": cases})
    save(output.with_name("local-gate-protocol.json"), protocol)


def analyze(panel_path, scores_path, output):
    panel, scores = read(panel_path), read(scores_path)
    if scores["panel_sha256"] != hashlib.sha256(panel_path.read_bytes()).hexdigest():
        raise ValueError("scores not bound to current capture")
    rows = []
    for case in panel["cases"]:
        hits = case["candidates"]
        values = scores["queries"][case["id"]]["scores"]
        if len(values) != len(hits) or not values or any(not math.isfinite(v) for v in values):
            raise ValueError("invalid complete local model response")
        chosen = sorted(range(len(values)), key=lambda i: (-values[i], i))[:8]
        selected = [hits[i] for i in chosen]
        if case["split"] == "negative" and any(
            h["filename"] != case["scope_filename"] for h in hits
        ):
            raise ValueError("unanswerable control escaped its document scope")
        old = sum(h["lexical_rank"] is not None for h in selected) / len(selected) >= 1 / 3
        new = sum(h["lexical_rank"] is not None for h in hits) / len(hits) >= 1 / 3
        floor = max(values) >= 0.02
        gold = any(h["chunk_id"] in case["gold_chunk_ids"] for h in selected)
        rows.append(
            {
                "id": case["id"],
                "article": case["article"],
                "split": case["split"],
                "gold8": gold,
                "old_admitted": old and floor,
                "new_admitted": new and floor,
                "old_gold_admitted": old and floor and gold,
                "new_gold_admitted": new and floor and gold,
            }
        )
    positive = [r for r in rows if r["split"] == "test"]
    negative = [r for r in rows if r["split"] == "negative"]
    if len(positive) != 128 or len(negative) != 32:
        raise ValueError("complete frozen cohort required")
    deltas = [int(r["new_gold_admitted"]) - int(r["old_gold_admitted"]) for r in positive]
    rng = random.Random(SEED)
    boots = sorted(sum(rng.choices(deltas, k=128)) / 128 for _ in range(2000))
    delta = sum(deltas) / 128
    old_negative = sum(r["old_admitted"] for r in negative)
    new_negative = sum(r["new_admitted"] for r in negative)
    result = {
        "protocol": panel["protocol"],
        "positive_cases": 128,
        "positive_article_clusters": 128,
        "negative_cases": 32,
        "positive": {
            key: sum(r[key] for r in positive)
            for key in positive[0]
            if key not in ["id", "article", "split"]
        },
        "negative_admitted": {"old": old_negative, "new": new_negative},
        "gold_admission_delta": delta,
        "paired_ci95": [boots[50], boots[1949]],
        "acceptance_met": delta >= 0.05 and new_negative <= old_negative,
        "panel_sha256": hashlib.sha256(panel_path.read_bytes()).hexdigest(),
        "scores_sha256": hashlib.sha256(scores_path.read_bytes()).hexdigest(),
        "cases": rows,
        "limits": [
            "admission and retrieval, not generated-answer correctness",
            "negative admission is not a false generated answer",
            "scoped unanswerable controls do not establish global out-of-domain behavior",
        ],
    }
    save(output, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    first = sub.add_parser("prepare")
    for name in ["old", "sqac", "negative", "output"]:
        first.add_argument("--" + name, type=Path, required=True)
    second = sub.add_parser("analyze")
    for name in ["panel", "scores", "output"]:
        second.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.old, args.sqac, args.negative, args.output)
    else:
        analyze(args.panel, args.scores, args.output)
