"""Local-only ContractNLI evidence benchmark using the official development split.

The public corpus contains real legal documents. This command sends document text
only to the configured local TEI endpoint, never to an external judge.
"""

import argparse
import json
from pathlib import Path
from typing import cast

from eval.contract_nli_common import ARCHIVE_SHA256, DEV_SHA256, build_document, load_documents
from eval.qasper_trial import evaluate_papers, summarize

DATASET_URL = (
    "https://raw.githubusercontent.com/stanfordnlp/contract-nli/gh-pages/resources/contract-nli.zip"
)
TRIAL_VERSION = "zenith-r1-contract-nli-dev-v1"

__all__ = ["build_document", "load_documents", "run"]


def run(path: Path, *, tei_url: str) -> dict[str, object]:
    papers, label_counts, blank_spans = load_documents(path)
    evaluation = evaluate_papers(papers, tei_url=tei_url, source_version="contract-nli-v1")
    rows = cast(list[dict[str, object]], evaluation["cases"])
    evaluation["summary_by_choice"] = {
        choice: summarize([row for row in rows if row["label_choice"] == choice])
        for choice in ("Entailment", "Contradiction")
    }
    return {
        "trial_version": TRIAL_VERSION,
        "dataset_url": DATASET_URL,
        "archive_sha256": ARCHIVE_SHA256,
        "dev_sha256": DEV_SHA256,
        "selection": "all 61 ContractNLI official v1 development documents",
        "label_provenance": (
            "ContractNLI human hypothesis labels and character-index evidence spans"
        ),
        "label_counts": dict(label_counts),
        "blank_annotated_spans_skipped": blank_spans,
        "non_evidence_label_policy": "NotMentioned has no evidence target; excluded from recall",
        "external_processing": False,
        **evaluation,
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
