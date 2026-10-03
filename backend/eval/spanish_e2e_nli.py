"""Independent local sentence entailment; provider labels never enter the judge input."""

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any, cast

from eval.spanish_e2e import (
    ARTICLES,
    measure,
    normalized,
    paired_interval,
    save,
    sentences_of,
    spans_supported,
)


def claim_inputs(response: dict[str, Any]) -> list[dict[str, Any]]:
    if response["abstained"]:
        return []
    citations = {int(c["marker"]): c for c in response["citations"]}
    result: list[dict[str, Any]] = []
    for sentence in sentences_of(response["answer"]):
        numbers = sorted(
            {int(n) for match in ARTICLES.finditer(sentence) for n in match.group(1).split(",")}
        )
        premise = "\n\n".join(citations[n]["text"] for n in numbers if n in citations)
        result.append(
            {"claim": ARTICLES.sub("", sentence).strip(), "markers": numbers, "premise": premise}
        )
    return result


def apply_entailment(
    metrics: dict[str, Any], probabilities: list[float], threshold: float
) -> dict[str, Any]:
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("invalid independent entailment probability")
    supported = bool(probabilities) and all(p >= threshold for p in probabilities)
    return {
        **metrics,
        "nli_supported_sentence_fraction": sum(p >= threshold for p in probabilities)
        / len(probabilities)
        if probabilities
        else 0,
        "nli_minimum_entailment": min(probabilities, default=0),
        "entailed_grounded_reference_match": float(
            bool(metrics["grounded_reference_match"]) and supported
        ),
    }


def rank_measures(case: dict[str, Any], scores: list[float]) -> dict[str, float]:
    chosen = sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:8]
    relevant = [int(spans_supported(h, case)) for h in case["candidates"]]
    positives = len(case["gold_chunk_ids"])
    ideal = sum(1 / math.log2(i + 2) for i in range(min(8, positives)))
    return {
        "ndcg8": sum(relevant[i] / math.log2(rank + 2) for rank, i in enumerate(chosen)) / ideal
        if ideal
        else 0,
        "gold_span_recall8": sum(relevant[i] for i in chosen) / positives if positives else 0,
        "gold_span_hit8": float(any(relevant[i] for i in chosen)),
    }


def summarize(
    record: dict[str, Any], panels: dict[str, Any], scores: dict[str, Any]
) -> dict[str, Any]:
    cases = {c["id"]: c for c in panels["cases"] if c["split"] == "test"}
    rows = record["cases"]
    if (
        record["phase"] != "complete"
        or len(rows) != len(cases)
        or {r["id"] for r in rows} != set(cases)
    ):
        raise ValueError("incomplete generated-answer evaluation")
    for row in rows:
        for arm in ("bge", "jev"):
            row[arm].update(
                rank_measures(cases[row["id"]], scores[arm]["queries"][row["id"]]["scores"])
            )
    metrics = [
        "entailed_grounded_reference_match",
        "grounded_reference_match",
        "answer_token_f1",
        "cited_answer_token_f1",
        "reference_match",
        "nli_supported_sentence_fraction",
        "sentence_citation_coverage",
        "reference_source_citation_precision",
        "ndcg8",
        "gold_span_recall8",
        "gold_span_hit8",
        "abstained",
        "raw_fabricated_markers",
        "invalid_citations",
    ]
    summary: dict[str, Any] = {
        arm: {m: statistics.mean(float(row[arm][m]) for row in rows) for m in metrics}
        for arm in ("bge", "jev")
    }
    paired = {m: paired_interval(rows, m) for m in metrics}
    primary = paired[record["protocol"]["primary_metric"]]
    summary["paired_jev_minus_bge"] = paired
    summary["meaningful_gain_met"] = primary["delta"] >= 0.02 and primary["ci95"][0] > 0
    summary["clearly_larger_gain_met"] = primary["delta"] >= 0.05 and primary["ci95"][0] >= 0.02
    summary["protocol"] = record["protocol"]
    summary["upload"] = record["upload"]
    summary["paid_accounting"] = {
        k: scores["jev"][k]
        for k in ("cumulative_calls", "cumulative_dollars", "new_calls", "new_dollars")
    }
    summary["test_pairs"] = len(rows)
    summary["limits"] = [
        "reference matching misses valid paraphrases and does not alone establish correctness",
        "automatic NLI can make mistakes; no new human adjudication of generated claims",
        "test is public Spanish QA, not client contracts or legal accuracy",
        "staged real services with response caches; no simultaneous deployment latency claim",
        "depth 32 is experimental in both arms; it does not change product defaults",
    ]
    for arm in ("bge", "jev"):
        generation = [row[arm]["generation"] for row in rows if row[arm]["generation"]]
        summary[arm]["generation"] = {
            "called_cases": len(generation),
            "reused_identical_prompts": sum(g["reused_identical_prompt"] for g in generation),
            "maximum_prompt_tokens": max((g["prompt_tokens"] for g in generation), default=0),
            "length_limited_completions": sum(g["done_reason"] == "length" for g in generation),
            "median_original_generation_seconds": statistics.median(
                g["generation_seconds"] for g in generation
            )
            if generation
            else None,
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sanity-only", action="store_true")
    args = parser.parse_args()
    if not args.sanity_only and (args.results is None or args.output is None):
        parser.error("full evaluation requires --results and --output")
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    tokenizer: Any = cast(Any, AutoTokenizer).from_pretrained(
        str(args.model), local_files_only=True
    )
    model: Any = cast(Any, AutoModelForSequenceClassification).from_pretrained(
        str(args.model), local_files_only=True, torch_dtype=torch.float32
    )
    model.eval()
    labels = {str(value).casefold(): int(key) for key, value in model.config.id2label.items()}
    if "entailment" not in labels:
        raise ValueError("independent model does not declare its entailment label")
    entailment_index = labels["entailment"]

    def entail(premise: str, claim: str) -> tuple[float, int]:
        if not normalized(premise):
            return 0.0, 0
        hyp = tokenizer.encode(claim, add_special_tokens=False)
        available = 512 - len(hyp) - tokenizer.num_special_tokens_to_add(pair=True)
        if available < 32:
            raise ValueError("generated claim too long for untruncated independent inference")
        tokens = tokenizer.encode(premise, add_special_tokens=False)
        stride = max(1, available - min(64, available // 4))
        probabilities: list[float] = []
        for start in range(0, len(tokens), stride):
            window = tokenizer.decode(tokens[start : start + available], skip_special_tokens=True)
            inputs = tokenizer(window, claim, return_tensors="pt", truncation=False)
            # Decoding/re-encoding may split a token differently; reduce the source window
            # explicitly rather than asking the tokenizer to silently truncate the premise.
            if inputs["input_ids"].shape[1] > 512:
                window = tokenizer.decode(
                    tokens[start : start + max(1, available - 16)], skip_special_tokens=True
                )
                inputs = tokenizer(window, claim, return_tensors="pt", truncation=False)
            if inputs["input_ids"].shape[1] > 512:
                raise ValueError("independent source window exceeds the fixed budget")
            with torch.inference_mode():
                probabilities.append(
                    float(torch.softmax(model(**inputs).logits[0], dim=-1)[entailment_index])
                )
            if start + available >= len(tokens):
                break
        return max(probabilities), len(probabilities)

    # Sanity checks are unrelated Spanish facts, specified before evaluating either arm.
    positive = entail("La capital de España es Madrid.", "Madrid es la capital de España.")[0]
    negative = entail(
        "La capital de España es Madrid.", "Madrid es la capital de todos los países."
    )[0]
    if not positive >= 0.8 or not negative < 0.8:
        raise ValueError("independent Spanish entailment sanity check failed")
    if args.sanity_only:
        print(json.dumps({"positive": positive, "negative": negative, "sanity_passed": True}))
        return
    assert args.results is not None and args.output is not None
    source_hash = hashlib.sha256(args.results.read_bytes()).hexdigest()
    record = json.loads(args.results.read_text(encoding="utf-8"))
    panels = json.loads((args.results.parent / "candidates.json").read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in panels["cases"]}
    record["independent_nli"] = {
        "input_sha256": source_hash,
        "positive_sanity": positive,
        "negative_sanity": negative,
        "dtype": "float32",
        "device": "cpu",
    }
    for index, row in enumerate(record["cases"]):
        for arm in ("bge", "jev"):
            metrics = row[arm]
            metrics.update(measure(cases[row["id"]], metrics["response"], metrics["shortlist"]))
            checked: list[dict[str, Any]] = []
            for claim in claim_inputs(metrics["response"]):
                probability, windows = entail(claim["premise"], claim["claim"])
                checked.append(
                    {
                        "claim": claim["claim"],
                        "markers": claim["markers"],
                        "entailment": probability,
                        "source_windows": windows,
                    }
                )
            metrics.update(apply_entailment(metrics, [c["entailment"] for c in checked], 0.8))
            metrics["independent_claim_checks"] = checked
        save(args.output, record)
        print(json.dumps({"independently_checked_pairs": index + 1}), flush=True)
    parent = args.results.parent
    scores = {
        arm: json.loads((parent / f"{arm}-scores.json").read_text(encoding="utf-8"))
        for arm in ("bge", "jev")
    }
    save(args.output.with_name("e2e-summary.json"), summarize(record, panels, scores))


if __name__ == "__main__":
    main()
