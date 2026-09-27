"""R1 isolated grouping versus resegmented/re-embedded public-source trial.

The snapshot and source-span labels are fixed before scoring. This is exploratory:
one agent-labeled EPA page cannot qualify a new production segmentation default.
"""

import argparse
import hashlib
import json
import time
from pathlib import Path
from uuid import UUID, uuid5

from app.features.ingestion.chunking.chunker import chunk_stream
from app.features.ingestion.chunking.lossless import Source, atomic_spans, structural_groups
from eval.embedder import TeiEmbedder
from eval.evidence_common import (
    EMBED_MODEL,
    RENDER_BUDGET_TOKENS,
    TOP_K,
    TrialUnit,
    choose,
    covers_all,
    displayed_range,
    line_ranges,
    rank,
    rendered_token_counts,
)

SNAPSHOT_SHA256 = "94e65678ac85eb7aacbb351113021c29bda3a8b257e6a81b31b0e40f79176b5f"
SOURCE_URL = "https://www.epa.gov/ground-water-and-drinking-water/basic-information-about-lead-drinking-water"
TRIAL_VERSION = "zenith-r1-epa-lead-v1"
SOURCE_ID = uuid5(UUID("5544de04-df02-4f26-bbb3-c950ef8db1e1"), SOURCE_URL)

# Agent-reviewed spans in the frozen public snapshot, 1-based extracted-text lines.
# The labels were not independently adjudicated, and this is not a clinical test.
QUERIES = (
    (
        "boiling-and-formula",
        "Does boiling remove lead and which tap water should be used for baby formula?",
        (93,),
    ),
    (
        "shower-qualification",
        "Can children shower in water containing lead, and when might advice differ?",
        (68, 69),
    ),
    (
        "filter-care",
        "What must a filter do to reduce lead and what water must not pass through it?",
        (91,),
    ),
    (
        "children-exposure",
        "What blood lead level triggers public health action, and why can exposure "
        "have several sources?",
        (43, 44),
    ),
    (
        "lead-free",
        "What does lead-free mean for pipe surfaces compared with solder and flux?",
        (23,),
    ),
)


def run(snapshot: Path, *, tei_url: str) -> dict[str, object]:
    text = snapshot.read_text(encoding="utf-8")
    if hashlib.sha256(text.encode()).hexdigest() != SNAPSHOT_SHA256:
        raise ValueError("public snapshot changed; labels and model comparison are invalid")
    source = Source(
        SOURCE_ID, None, text, SNAPSHOT_SHA256, "zenith-eval-html-main-v1", "2026-09-26"
    )
    legacy: list[TrialUnit] = []
    for index, item in enumerate(chunk_stream(text)):
        start, end = displayed_range(text, item.char_start, item.char_end)
        if text[start:end] != item.text:
            raise ValueError("legacy chunk display text does not match source coordinates")
        legacy.append(TrialUnit(str(index), start, end, item.text))
    groups = [
        TrialUnit(str(item.id), item.start, item.end, item.text)
        for item in structural_groups(
            source, atomic_spans(source, max_chars=1000), target_chars=1200, max_chars=1600
        )
    ]
    if not legacy or not groups:
        raise ValueError("trial has no segments")
    embedder = TeiEmbedder(tei_url)
    started = time.perf_counter()
    token_counts = rendered_token_counts(legacy + groups, tei_url)
    tokenization_ms = round((time.perf_counter() - started) * 1000)
    started = time.perf_counter()
    legacy_vectors = embedder.encode([item.text for item in legacy], batch=4)
    legacy_embed_ms = round((time.perf_counter() - started) * 1000)
    started = time.perf_counter()
    group_vectors = embedder.encode([item.text for item in groups], batch=4)
    group_embed_ms = round((time.perf_counter() - started) * 1000)
    query_vectors = embedder.encode([query for _, query, _ in QUERIES], batch=4)
    lines = line_ranges(text)
    rows: list[dict[str, object]] = []
    for (name, query, line_numbers), query_vector in zip(QUERIES, query_vectors, strict=True):
        gold = tuple(displayed_range(text, *lines[number - 1]) for number in line_numbers)
        legacy_ranked = rank(legacy, legacy_vectors, query_vector)
        group_ranked = rank(groups, group_vectors, query_vector)
        # R1a keeps the legacy retrieval leaders fixed, then expands them to groups.
        leader_order = {item.id: position for position, item in enumerate(legacy_ranked)}
        grouped_from_legacy = sorted(
            groups,
            key=lambda group: (
                min(
                    (
                        leader_order[item.id]
                        for item in legacy
                        if item.start < group.end and item.end > group.start
                    ),
                    default=len(legacy),
                ),
                group.start,
            ),
        )
        outcomes: dict[str, object] = {}
        for route, ranked in (
            ("legacy", legacy_ranked),
            ("grouped_from_legacy", grouped_from_legacy),
            ("resegmented_reembedded", group_ranked),
        ):
            selected = choose(ranked, token_counts=token_counts)
            outcomes[route] = {
                "complete_gold_spans": covers_all(selected, gold),
                "top1_intersects_gold": any(
                    ranked[0].start < end and ranked[0].end > start for start, end in gold
                ),
                "rendered_characters": sum(len(item.text) for item in selected),
                "rendered_tokens": sum(token_counts[item.id] for item in selected),
                "selected_segment_ids": [item.id for item in selected],
            }
        rows.append(
            {"id": name, "question": query, "gold_lines": list(line_numbers), "routes": outcomes}
        )
    return {
        "trial_version": TRIAL_VERSION,
        "source_url": SOURCE_URL,
        "source_text_sha256": SNAPSHOT_SHA256,
        "label_provenance": "agent-reviewed exact extracted-line labels; exploratory",
        "embedding_model": EMBED_MODEL,
        "embedding_endpoint": tei_url,
        "segmentation_version": "zenith-structural-v1",
        "render_budget_tokens": RENDER_BUDGET_TOKENS,
        "tokenizer": EMBED_MODEL,
        "tokenization_ms": tokenization_ms,
        "top_k": TOP_K,
        "legacy_segments": len(legacy),
        "structural_segments": len(groups),
        "legacy_embedding_ms": legacy_embed_ms,
        "structural_embedding_ms": group_embed_ms,
        "queries": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--tei-url", default="http://127.0.0.1:18081")
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    report = run(options.snapshot, tei_url=options.tei_url)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {options.output}")


if __name__ == "__main__":
    main()
