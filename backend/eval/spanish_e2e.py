"""Published Spanish answer spans and explicitly limited automatic citation measures."""

import hashlib
import json
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

SEED = 20261002
ARTICLES = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", ARTICLES.sub("", value)).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in value).split())


def token_f1(answer: str, expected: str) -> float:
    left, right = normalized(answer).split(), normalized(expected).split()
    if not left or not right:
        return float(left == right)
    overlap = sum((Counter(left) & Counter(right)).values())
    return 2 * overlap / (len(left) + len(right))


def contexts(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    unique: dict[str, dict[str, Any]] = {}
    for article in payload["data"]:
        for paragraph in article["paragraphs"]:
            raw = paragraph["context"]
            value = raw.replace("\r\n", "\n").replace("\r", "\n")
            key = sha(value)
            current = unique.setdefault(
                key, {"key": key, "text": value, "title": article["title"], "questions": []}
            )
            for qa in paragraph["qas"]:
                answers: list[dict[str, Any]] = []
                for gold in qa["answers"]:
                    start, text = gold["answer_start"], gold["text"]
                    if raw[start : start + len(text)] != text:
                        raise ValueError(f"invalid published answer offset: {qa['id']}")
                    begin = len(raw[:start].replace("\r\n", "\n").replace("\r", "\n"))
                    clean = text.replace("\r\n", "\n").replace("\r", "\n")
                    answers.append({"text": clean, "start": begin, "end": begin + len(clean)})
                if not answers:
                    raise ValueError("SQAC answerable fixture lacks published answer")
                current["questions"].append(
                    {"id": qa["id"], "question": qa["question"], "answers": answers}
                )
    return sorted(unique.values(), key=lambda row: sha(f"{SEED}|{row['key']}"))


def prepare(dev: Path, test: Path, output: Path, test_count: int = 128) -> dict[str, Any]:
    development, testing = contexts(dev), contexts(test)
    if {r["key"] for r in development} & {r["key"] for r in testing}:
        raise ValueError("development/test context overlap")
    if len(testing) < test_count:
        raise ValueError("insufficient held-out contexts")
    selected = {"development": development[:16], "test": testing[:test_count]}
    corpus = sorted(testing + selected["development"], key=lambda r: r["key"])
    ranges: dict[str, int] = {}
    pieces: list[str] = []
    offset = 0
    for row in corpus:
        ranges[row["key"]] = offset
        pieces.append(row["text"])
        offset += len(row["text"]) + 2
    value = "\n\n".join(pieces)
    # The monolithic initial upload hit the existing embedding INSERT timeout. Retain
    # all corpus texts and selected questions, but bound files at context boundaries.
    documents: list[dict[str, Any]] = []
    filenames: dict[str, str] = {}
    for row in corpus:
        if not documents or len(documents[-1]["text"]) + 2 + len(row["text"]) > 64000:
            documents.append({"filename": f"sqac-public-{len(documents):03d}.txt", "text": ""})
        document = documents[-1]
        separator = "\n\n" if document["text"] else ""
        ranges[row["key"]] = len(document["text"]) + len(separator)
        filenames[row["key"]] = document["filename"]
        document["text"] += separator + row["text"]
    assert "\n\n".join(d["text"] for d in documents) == value
    cases: list[dict[str, Any]] = []
    for split, rows in selected.items():
        for row in rows:
            qa = min(row["questions"], key=lambda q: sha(f"{SEED}|{q['id']}"))
            if len(qa["question"]) > 1000:
                raise ValueError("published question exceeds actual query route limit")
            cases.append(
                {
                    "id": qa["id"],
                    "question": qa["question"],
                    "split": split,
                    "context_key": row["key"],
                    "filename": filenames[row["key"]],
                    "article": sha(row["title"]),
                    "answers": [
                        {
                            "text": a["text"],
                            "start": a["start"] + ranges[row["key"]],
                            "end": a["end"] + ranges[row["key"]],
                        }
                        for a in qa["answers"]
                    ],
                }
            )
    if len({c["question"] for c in cases}) != len(cases):
        raise ValueError("duplicate questions need explicit multi-reference grouping")
    protocol = {
        "seed": SEED,
        "test_cases": test_count,
        "development_cases": 16,
        "corpus_contexts": len(corpus),
        "corpus_sha256": sha(value),
        "corpus_bytes": len(value.encode()),
        "document_count": len(documents),
        "document_layout": "target 64000 characters, split only between published contexts",
        "retrieved_candidates": 32,
        "generated_passages": 8,
        "batch_tokens": 1024,
        "batch_items": 2,
        "source_sha256": {
            "dev": hashlib.sha256(dev.read_bytes()).hexdigest(),
            "test": hashlib.sha256(test.read_bytes()).hexdigest(),
        },
        "generator": {
            "model": "qwen3:4b",
            "model_digest": "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7",
            "thinking": False,
            "temperature": 0,
            "seed": SEED,
            "num_ctx": 8192,
            "num_predict": 256,
        },
        "meaningful_gain": {"mean": 0.02, "lower_ci_above": 0},
        "clearly_larger_gain": {"mean": 0.05, "lower_ci_at_least": 0.02},
        "primary_metric": "entailed_grounded_reference_match",
        "reference_span_metric": "grounded_reference_match",
        "nli": {
            "model": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
            "revision": "8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c",
            "entailment_threshold": 0.8,
            "maximum_tokens": 512,
            "truncation": "none; split long premises into overlapping token windows",
            "limits": "independent automatic multilingual NLI, not human claim adjudication",
        },
        "limits": [
            "automatic reference/span proxies, not full semantic adjudication",
            "staged model execution, not simultaneous online latency",
            "experimental depth 32; production CPU depth is eight",
        ],
    }
    payload: dict[str, Any] = {
        "protocol": protocol,
        "corpus": value,
        "documents": documents,
        "cases": cases,
    }
    save(output, payload)
    save(output.with_name("preregistered-protocol.json"), protocol)
    return protocol


def spans_supported(hit: dict[str, Any], case: dict[str, Any]) -> bool:
    if case.get("filename") and hit.get("filename") != case["filename"]:
        return False
    return any(
        hit["char_start"] <= a["start"]
        and hit["char_end"] >= a["end"]
        and normalized(a["text"]) in normalized(hit["text"])
        for a in case["answers"]
    )


def sentences_of(answer: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÜÑ¿¡])|\n+", answer) if normalized(s)]


def sentence_coverage(answer: str) -> float:
    sentences = sentences_of(answer)
    return sum(bool(ARTICLES.search(s)) for s in sentences) / len(sentences) if sentences else 0.0


def measure(
    case: dict[str, Any], response: dict[str, Any], shortlist: list[dict[str, Any]]
) -> dict[str, Any]:
    citations = response["citations"]
    available = {h["chunk_id"]: h for h in shortlist}
    valid = all(
        c["chunk_id"] in available
        and c["document_id"] == available[c["chunk_id"]]["document_id"]
        and c["char_start"] == available[c["chunk_id"]]["char_start"]
        and c["char_end"] == available[c["chunk_id"]]["char_end"]
        and c["text"] == available[c["chunk_id"]]["text"]
        for c in citations
    )
    supported = [spans_supported(c, case) for c in citations]
    answer = response["answer"]
    contains = (
        any(normalized(a["text"]) in normalized(answer) for a in case["answers"])
        and not response["abstained"]
    )
    coverage = sentence_coverage(answer) if not response["abstained"] else 0.0
    aligned = any(
        normalized(a["text"]) in normalized(answer)
        and any(
            c["char_start"] <= a["start"]
            and c["char_end"] >= a["end"]
            and normalized(a["text"]) in normalized(c["text"])
            for c in citations
        )
        for a in case["answers"]
    )
    grounded = contains and aligned and valid and coverage == 1.0
    f1 = (
        max(token_f1(answer, a["text"]) for a in case["answers"])
        if not response["abstained"]
        else 0
    )
    return {
        "grounded_reference_match": float(grounded),
        "reference_match": float(contains),
        "answer_token_f1": f1,
        "cited_answer_token_f1": f1 if any(supported) and valid else 0,
        "reference_source_citation_precision": sum(supported) / len(supported) if supported else 0,
        "sentence_citation_coverage": coverage,
        "invalid_citations": int(not valid),
        "abstained": int(response["abstained"]),
        "citation_count": len(citations),
    }


def paired_interval(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    groups: dict[str, list[float]] = {}
    for row in rows:
        delta = row["jev"][metric] - row["bge"][metric]
        groups.setdefault(row["article"], []).append(delta)
    rng, values = random.Random(SEED), list(groups.values())
    draws: list[float] = []
    if not values:
        raise ValueError("empty paired evaluation")
    for _ in range(2000):
        selected = [rng.choice(values) for _ in values]
        total = sum(len(v) for v in selected)
        draws.append(sum(sum(v) for v in selected) / total)
    draws.sort()
    return {
        "delta": sum(sum(v) for v in values) / sum(map(len, values)),
        "ci95": [draws[49], draws[1949]],
        "article_clusters": len(values),
        "samples": len(rows),
    }
