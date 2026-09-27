"""Bounded, source-preserving ES/EN transfer trial for R1 and packet selection.

Uses the original extractive span from public RAG_Multilingual QA examples, not
the model-written expanded answer. The alternate structural index is built and
ranked independently. No Jev request or tenant document is involved.
"""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportMissingTypeStubs=false

import argparse
import asyncio
import hashlib
import json
import re
import statistics
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import NAMESPACE_URL, UUID, uuid5

from app.core.hardware import PROFILES
from app.features.generation.answering import packet
from app.features.ingestion.chunking.chunker import chunk_stream
from app.features.ingestion.chunking.lossless import Source, atomic_spans, structural_groups
from app.features.retrieval.reranker import MODEL as RERANK_MODEL
from app.features.retrieval.reranker import TeiReranker
from app.features.retrieval.search import Hit
from app.features.tenancy.context import TenantContext
from eval.evidence_common import TrialUnit, displayed_range, rendered_token_counts

DATASET = "projecte-aina/RAG_Multilingual"
REVISION = "a7020cfffaeff43c23f2847da0b45df51a49faf3"
LICENSE = "CC-BY-SA-4.0"
VERSION = "zenith-rag-multilingual-structural-packets-transfer-v2"
TEI_URL = "http://127.0.0.1:18083"
BUDGET = 512
TOP_K = 8
COUNTS = {"validation": 8, "test": 12}  # per language
EXCEPTION = re.compile(r"\b(?:except|unless|however|salvo|excepto|sin embargo)\b", re.I)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def rows(path: Path) -> tuple[str, dict[str, dict[str, str]]]:
    raw = path.read_bytes()
    result: dict[str, dict[str, str]] = {}
    for line in raw.splitlines():
        item: dict[str, Any] = json.loads(line)
        if item.get("lang") not in {"es", "en"}:
            continue
        context = item.get("context")
        answer = item.get("extractive")
        question = item.get("instruction")
        if not all(isinstance(value, str) for value in (context, answer, question)):
            continue
        context, answer, question = str(context), str(answer), str(question)
        if not 1000 <= len(context) <= 4000 or not answer or len(question) > 220:
            continue
        if len(list(re.finditer(re.escape(answer), context, re.I))) != 1:
            continue
        result[str(item["id"])] = {
            "context": context,
            "answer": answer,
            "question": question,
            "lang": str(item["lang"]),
        }
    return digest(raw), result


def freeze(data: Path, output: Path) -> dict[str, object]:
    if output.exists():
        raise ValueError("frozen manifest exists")
    sources: dict[str, dict[str, dict[str, str]]] = {}
    file_hashes: dict[str, str] = {}
    for split in COUNTS:
        file_hashes[split], sources[split] = rows(data / f"{split}.jsonl")
    selected: dict[str, list[dict[str, object]]] = {}
    for split, count in COUNTS.items():
        selected[split] = []
        for lang in ("es", "en"):
            candidates = sorted(
                (
                    (identity, row)
                    for identity, row in sources[split].items()
                    if row["lang"] == lang
                ),
                key=lambda pair: digest(f"{VERSION}:{split}:{pair[0]}".encode()),
            )
            seen: set[str] = set()
            chosen = 0
            for identity, row in candidates:
                context_hash = digest(row["context"].encode())
                if context_hash in seen:
                    continue
                distractors = sorted(
                    (
                        other_id
                        for other_id, other in sources[split].items()
                        if other["lang"] == lang
                        and other_id != identity
                        and row["answer"].casefold() not in other["context"].casefold()
                        and digest(other["context"].encode()) != context_hash
                    ),
                    key=lambda other_id: digest(f"{VERSION}:{identity}:{other_id}".encode()),
                )[:3]
                if len(distractors) != 3:
                    continue
                selected[split].append(
                    {
                        "id": identity,
                        "language": lang,
                        "context_sha256": context_hash,
                        "distractors": distractors,
                    }
                )
                seen.add(context_hash)
                chosen += 1
                if chosen == count:
                    break
            if chosen != count:
                raise ValueError(f"too few eligible {split}/{lang} records")
    dev_hashes = {str(row["context_sha256"]) for row in selected["validation"]}
    if dev_hashes.intersection(str(row["context_sha256"]) for row in selected["test"]):
        raise ValueError("development and test share source context")
    manifest: dict[str, object] = {
        "version": VERSION,
        "source": DATASET,
        "revision": REVISION,
        "license": LICENSE,
        "label_provenance": (
            "source extractive QA spans reviewed by humans; expanded responses unused"
        ),
        "file_sha256": file_hashes,
        "selection": selected,
        "routes": ["flat_bge", "structural_reindexed_bge", "flat_packet", "flat_packet_counter"],
        "candidate_sources_per_case": 4,
        "budget_bge_tokens": BUDGET,
        "top_k": TOP_K,
        "reranker": RERANK_MODEL,
        "reranker_endpoint": TEI_URL,
        "serving_image": "ghcr.io/huggingface/text-embeddings-inference:120-1.9",
        "postfreeze_revisions_allowed": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def segments(identity: str, context: str, structural: bool) -> list[Hit]:
    document = uuid5(NAMESPACE_URL, f"{DATASET}:{REVISION}:{identity}")
    source_hash = digest(context.encode())
    units: list[TrialUnit]
    if structural:
        source = Source(document, None, context, source_hash, "rag-multilingual-v1", REVISION)
        groups = structural_groups(
            source, atomic_spans(source, max_chars=1000), target_chars=1200, max_chars=1600
        )
        units = [TrialUnit(str(group.id), group.start, group.end, group.text) for group in groups]
    else:
        units = []
        for index, item in enumerate(chunk_stream(context)):
            start, end = displayed_range(context, item.char_start, item.char_end)
            units.append(TrialUnit(str(index), start, end, item.text))
    if not units or any(context[unit.start : unit.end] != unit.text for unit in units):
        raise ValueError("source-preserving segment map failed")
    return [
        Hit(
            chunk_id=uuid5(NAMESPACE_URL, f"{document}:{structural}:{unit.id}"),
            document_id=document,
            filename=f"{identity}.txt",
            media_type="text/plain",
            page_num=None,
            char_start=unit.start,
            char_end=unit.end,
            text=unit.text,
            bboxes=[],
            lexical_rank=None,
            dense_rank=None,
            score=0.0,
            source_sha256=source_hash,
        )
        for unit in units
    ]


def outcome(
    selected: list[Hit], target: UUID, gold: tuple[int, int], costs: dict[UUID, int]
) -> dict[str, Any]:
    ranges = sorted(
        (int(hit.char_start), int(hit.char_end)) for hit in selected if hit.document_id == target
    )
    merged: list[list[int]] = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return {
        "complete_evidence": any(start <= gold[0] and end >= gold[1] for start, end in merged),
        "top1_evidence": bool(
            selected
            and selected[0].document_id == target
            and selected[0].char_start < gold[1]
            and selected[0].char_end > gold[0]
        ),
        "rendered_tokens": sum(costs[hit.chunk_id] for hit in selected),
        "selected_units": len(selected),
    }


def within_budget(ranked: list[Hit], costs: dict[UUID, int]) -> list[Hit]:
    selected: list[Hit] = []
    spent = 0
    for hit in ranked[:TOP_K]:
        cost = costs[hit.chunk_id]
        if spent + cost <= BUDGET:
            selected.append(hit)
            spent += cost
    return selected


async def packet_route(
    question: str,
    ranked: list[Hit],
    all_hits: list[Hit],
    costs: dict[UUID, int],
    *,
    counterevidence: bool,
) -> packet.EvidencePacket:
    by_source: dict[UUID, list[Hit]] = {}
    for hit in all_hits:
        by_source.setdefault(hit.document_id, []).append(hit)
    positions = {
        hit.chunk_id: index for group in by_source.values() for index, hit in enumerate(group)
    }

    async def neighbor(context: TenantContext, hit: Hit, *, before: bool) -> Hit | None:
        group = by_source[hit.document_id]
        index = positions[hit.chunk_id] + (-1 if before else 1)
        return group[index] if 0 <= index < len(group) else None

    async def referenced(context: TenantContext, hit: Hit, reference: str) -> Hit | None:
        return None

    async def counter(
        context: TenantContext, hit: Hit, excluded: set[UUID], cap: int
    ) -> tuple[Hit, ...]:
        return tuple(
            item
            for item in by_source[hit.document_id]
            if item.chunk_id not in excluded and EXCEPTION.search(item.text)
        )[:cap]

    def render_cost(hits: list[Hit], reasons: list[str]) -> int:
        return sum(costs[hit.chunk_id] for hit in hits)

    with (
        patch.object(packet, "_neighbor", neighbor),
        patch.object(packet, "_referenced", referenced),
        patch.object(packet, "_counter_candidates", counter),
    ):
        return await packet.build_packet(
            TenantContext.for_tenant(uuid5(NAMESPACE_URL, "rag-transfer-disposable")),
            question,
            ranked[:TOP_K],
            token_budget=BUDGET,
            render_cost=render_cost,
            cost_unit="bge_m3_source_tokens",
            counterevidence=counterevidence,
            max_counterevidence=2,
        )


async def run(data: Path, manifest_path: Path, output: Path) -> dict[str, object]:
    if output.exists():
        raise ValueError("trial result exists; locked set is one-shot")
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != VERSION or manifest.get("budget_bge_tokens") != BUDGET:
        raise ValueError("trial protocol changed after freeze")
    source_rows: dict[str, dict[str, dict[str, str]]] = {}
    for split in COUNTS:
        actual, source_rows[split] = rows(data / f"{split}.jsonl")
        if actual != manifest["file_sha256"][split]:
            raise ValueError("source file changed after freeze")
    reranker = TeiReranker(url=TEI_URL, profile=PROFILES["gpu"])
    report: dict[str, Any] = {
        "version": VERSION,
        "manifest_sha256": digest(manifest_path.read_bytes()),
        "model": RERANK_MODEL,
        "rows": {},
        "summary": {},
    }
    for split in COUNTS:
        outputs: list[dict[str, Any]] = []
        for case in manifest["selection"][split]:
            identity = str(case["id"])
            row = source_rows[split][identity]
            if digest(row["context"].encode()) != case["context_sha256"]:
                raise ValueError("selected source hash changed")
            source_ids = [identity, *case["distractors"]]
            flat = [
                hit
                for source_id in source_ids
                for hit in segments(source_id, source_rows[split][source_id]["context"], False)
            ]
            structural = [
                hit
                for source_id in source_ids
                for hit in segments(source_id, source_rows[split][source_id]["context"], True)
            ]
            all_hits = flat + structural
            counts = rendered_token_counts(
                [
                    TrialUnit(str(hit.chunk_id), hit.char_start, hit.char_end, hit.text)
                    for hit in all_hits
                ],
                TEI_URL,
            )
            costs = {hit.chunk_id: counts[str(hit.chunk_id)] for hit in all_hits}
            started = time.perf_counter()
            flat_order = await reranker.rank(row["question"], [hit.text for hit in flat])
            structural_order = await reranker.rank(
                row["question"], [hit.text for hit in structural]
            )
            flat_ranked = [flat[item.index] for item in flat_order]
            structural_ranked = [structural[item.index] for item in structural_order]
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            target = uuid5(NAMESPACE_URL, f"{DATASET}:{REVISION}:{identity}")
            match = re.search(re.escape(row["answer"]), row["context"], re.I)
            if match is None:
                raise ValueError("frozen extractive span missing")
            gold = match.span()
            plain = await packet_route(
                row["question"], flat_ranked, flat, costs, counterevidence=False
            )
            counter = await packet_route(
                row["question"], flat_ranked, flat, costs, counterevidence=True
            )
            routes = {
                "flat_bge": outcome(within_budget(flat_ranked, costs), target, gold, costs),
                "structural_reindexed_bge": outcome(
                    within_budget(structural_ranked, costs), target, gold, costs
                ),
                "flat_packet": outcome(list(plain.hits), target, gold, costs),
                "flat_packet_counter": outcome(list(counter.hits), target, gold, costs),
            }
            if any(int(result["rendered_tokens"]) > BUDGET for result in routes.values()):
                raise ValueError("route exceeded the matched context budget")
            outputs.append(
                {
                    "id": identity,
                    "language": row["lang"],
                    "context_sha256": case["context_sha256"],
                    "gold_sha256": digest(row["answer"].encode()),
                    "model_ms": elapsed_ms,
                    "flat_segments": len(flat),
                    "structural_segments": len(structural),
                    "routes": routes,
                }
            )
            print(f"{split} {len(outputs)}/{len(manifest['selection'][split])}", flush=True)
        report["rows"][split] = outputs
        report["summary"][split] = {
            name: {
                "cases": len(outputs),
                "complete": sum(
                    bool(item["routes"][name]["complete_evidence"]) for item in outputs
                ),
                "top1": sum(bool(item["routes"][name]["top1_evidence"]) for item in outputs),
                "mean_tokens": statistics.mean(
                    int(item["routes"][name]["rendered_tokens"]) for item in outputs
                ),
            }
            for name in manifest["routes"]
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run"))
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    if options.action == "freeze":
        freeze(options.data, options.manifest)
        print(digest(options.manifest.read_bytes()))
    else:
        if options.output is None:
            raise ValueError("run requires --output")
        asyncio.run(run(options.data, options.manifest, options.output))


if __name__ == "__main__":
    main()
