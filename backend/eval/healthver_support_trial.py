"""Frozen public HealthVer support transfer; opt-in live Jev calls only.

Uses original expert-labeled claim/evidence pairs. Samples disjoint claims and
evidence across development and test. No corpus text is committed or logged.
"""

import argparse
import asyncio
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.core.config import settings
from app.features.retrieval.judging.jev import JevJudge, JevQuota, ProcessingPolicy, Purpose
from app.features.retrieval.judging.protocol import Candidate
from app.features.retrieval.judging.rubrics import CLAIM_SUPPORT_NOUL, Formulation

VERSION = "healthver-support-transfer-v1"
SOURCE_COMMIT = "b20ac99ceed62f5264a319fa25a854df1668d85b"
MODEL = "jev-1.13.0"
LABELS = ("Supports", "Refutes", "Neutral")
SPLITS = {"dev": 4, "test": 8}  # per label, 36 calls total
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_new(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as out:
        json.dump(obj, out, indent=2)
        out.write("\n")


def append(path: Path, obj: object) -> None:
    with path.open("a", encoding="utf-8") as out:
        out.write(json.dumps(obj) + "\n")
        out.flush()
        os.fsync(out.fileno())


def source_rows(root: Path, split: str) -> tuple[str, list[dict[str, str]]]:
    path = root / f"healthver_{split}.csv"
    raw = path.read_bytes()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return sha(raw), [row for row in rows if row["label"] in LABELS]


def freeze(root: Path, output: Path) -> None:
    selected: dict[str, list[dict[str, str]]] = {}
    hashes: dict[str, str] = {}
    seen_claims: set[str] = set()
    seen_evidence: set[str] = set()
    for split, count in SPLITS.items():
        hashes[split], rows = source_rows(root, split)
        selected[split] = []
        for label in LABELS:
            options = sorted(
                (row for row in rows if row["label"] == label),
                key=lambda row: sha(f"{VERSION}:{split}:{row['id']}".encode()),
            )
            chosen = 0
            for row in options:
                claim_hash = sha(row["claim"].encode())
                evidence_hash = sha(row["evidence"].encode())
                if not row["claim"] or not row["evidence"]:
                    continue
                if claim_hash in seen_claims or evidence_hash in seen_evidence:
                    continue
                selected[split].append(
                    {
                        "id": row["id"],
                        "label": label,
                        "claim_sha256": claim_hash,
                        "evidence_sha256": evidence_hash,
                    }
                )
                seen_claims.add(claim_hash)
                seen_evidence.add(evidence_hash)
                chosen += 1
                if chosen == count:
                    break
            if chosen != count:
                raise ValueError(f"insufficient unique {split}/{label}")
    manifest = {
        "version": VERSION,
        "source": "sarrouti/HealthVer",
        "source_commit": SOURCE_COMMIT,
        "file_sha256": hashes,
        "selected": selected,
        "calls_reserved": sum(len(x) for x in selected.values()),
        "threshold_candidates": THRESHOLDS,
        "threshold_rule": (
            "On dev, minimize Refutes+Neutral accepted; tie maximize Supports accepted; "
            "final tie highest threshold. Evaluate selected threshold once on test. "
            "Retain production 0.8 regardless."
        ),
        "authorization": (
            "within user's 320 calls/$3 pilot; strict support purpose cap 64, "
            "24 prior calls, 36 this run; no retries"
        ),
        "capture": "hashes, labels, rank values, usage; no raw text or responses",
    }
    write_new(output, manifest)
    print(sha(output.read_bytes()))


async def run(root: Path, manifest_path: Path, expected_sha: str) -> None:
    if sha(manifest_path.read_bytes()) != expected_sha:
        raise ValueError("frozen manifest hash changed")
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["version"] != VERSION or manifest["source_commit"] != SOURCE_COMMIT:
        raise ValueError("unexpected manifest")
    ledger = manifest_path.parent / "ledger.jsonl"
    if ledger.exists():
        raise ValueError("existing ledger; uncertain requests may not be replayed")
    if not settings.jev_api_key:
        raise ValueError("Jev credential unavailable")
    selected: list[tuple[str, dict[str, str], dict[str, str]]] = []
    for split in SPLITS:
        file_hash, rows = source_rows(root, split)
        if file_hash != manifest["file_sha256"][split]:
            raise ValueError("source changed")
        by_id = {row["id"]: row for row in rows}
        for item in manifest["selected"][split]:
            row = by_id[item["id"]]
            if sha(row["claim"].encode()) != item["claim_sha256"]:
                raise ValueError("claim changed")
            if sha(row["evidence"].encode()) != item["evidence_sha256"]:
                raise ValueError("evidence changed")
            selected.append((split, item, row))
    if len(selected) != 36 or manifest["calls_reserved"] != 36:
        raise ValueError("call count changed")

    async def allowed(question: str, candidate: Candidate, purpose: Purpose) -> bool:
        return purpose == Purpose.CLAIM_SUPPORT

    quota = JevQuota(36, 180_000, max_concurrency=2)
    judge = JevJudge(
        api_key=settings.jev_api_key.get_secret_value(),
        model=MODEL,
        formulation=Formulation.NOUL,
        rubric=CLAIM_SUPPORT_NOUL,
        policy=ProcessingPolicy(claim_support=True),
        purpose=Purpose.CLAIM_SUPPORT,
        authorize=allowed,
        quota=quota,
        max_concurrency=2,
        max_retries=0,
    )
    append(ledger, {"event": "start", "manifest_sha256": expected_sha})
    try:
        for split, item, row in selected:
            append(ledger, {"event": "reserved", "split": split, "id": item["id"]})
            candidate = Candidate(uuid5(NAMESPACE_URL, f"{VERSION}:{item['id']}"), row["evidence"])
            batch = await judge.assess(row["claim"], [candidate])
            result = batch.judgments[0]
            append(
                ledger,
                {
                    "event": "result",
                    "split": split,
                    "id": item["id"],
                    "label": item["label"],
                    "outcome": result.outcome.value,
                    "failure": result.failure_code,
                    "rank_value": result.rank_value,
                    "input_tokens": batch.usage,
                    "output_tokens": batch.output_tokens,
                },
            )
    finally:
        await judge.aclose()
    append(
        ledger, {"event": "complete", "calls": quota.requests, "input_tokens": quota.input_tokens}
    )


def report(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [json.loads(x) for x in (manifest_path.parent / "ledger.jsonl").read_text().splitlines()]
    if rows[-1]["event"] != "complete":
        raise ValueError("run incomplete")
    observations = [x for x in rows if x["event"] == "result"]
    if len(observations) != manifest["calls_reserved"]:
        raise ValueError("missing observations")

    def counts(split: str, threshold: float) -> dict[str, dict[str, int]]:
        output = {label: {"accepted": 0, "total": 0, "invalid": 0} for label in LABELS}
        for row in observations:
            if row["split"] != split:
                continue
            slot = output[row["label"]]
            slot["total"] += 1
            valid = row["outcome"] == "assessed" and isinstance(row["rank_value"], (int, float))
            slot["invalid"] += int(not valid)
            slot["accepted"] += int(valid and row["rank_value"] >= threshold)
        return output

    dev = {str(t): counts("dev", t) for t in THRESHOLDS}
    selected_threshold = min(
        THRESHOLDS,
        key=lambda t: (
            dev[str(t)]["Refutes"]["accepted"] + dev[str(t)]["Neutral"]["accepted"],
            -dev[str(t)]["Supports"]["accepted"],
            -t,
        ),
    )
    output = {
        "manifest_sha256": sha(manifest_path.read_bytes()),
        "source_commit": SOURCE_COMMIT,
        "selection": "disjoint claim and evidence hashes; labels stratified before calls",
        "dev_thresholds": dev,
        "selected_threshold": selected_threshold,
        "test_selected": counts("test", selected_threshold),
        "test_current_0_8": counts("test", 0.8),
        "accounting": rows[-1],
    }
    write_new(manifest_path.parent / "result.json", output)
    print(json.dumps(output, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run", "report"))
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", default="")
    options = parser.parse_args()
    if ".scratch" not in options.manifest.resolve().parts:
        raise ValueError("manifest must stay under ignored .scratch")
    if options.action == "freeze":
        freeze(options.data, options.manifest)
    elif options.action == "run":
        asyncio.run(run(options.data, options.manifest, options.manifest_sha256))
    else:
        report(options.manifest)


if __name__ == "__main__":
    main()
