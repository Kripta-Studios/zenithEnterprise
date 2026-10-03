"""Inventory pinned public Spanish datasets without invoking any inference provider."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / ".local-data" / "spanish"
SOURCES = {
    "sqac": ("PlanTL-GOB-ES/SQAC", "f9928e8819596a601b8887cc5f8598b15d589a82"),
    "alia-cqa": (
        "SINAI/ALIA-es-legal-administrative-cqa",
        "eeb7de37cdccebed7b29fa9f6a86cd8747145e43",
    ),
    "alia-triplets": (
        "SINAI/ALIA-es-legal-administrative-triplets",
        "0a3753db69cd99923f953b8a3fde3d42fb6e8ca8",
    ),
    "miracl-es": ("miracl/miracl", "5be20db9509754dadad47689368639fcec739c00"),
}


def main() -> None:
    manifest = {"provider_calls": 0, "datasets": []}
    for directory, (repo, revision) in SOURCES.items():
        files = []
        for path in sorted((DATA / directory).rglob("*")):
            if not path.is_file() or ".cache" in path.parts:
                continue
            files.append(
                {
                    "path": path.relative_to(DATA).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        manifest["datasets"].append(
            {
                "repository": repo,
                "revision": revision,
                "source": f"https://huggingface.co/datasets/{repo}/tree/{revision}",
                "files": files,
            }
        )
    sqac = {}
    for split in ("dev", "test"):
        payload = json.loads((DATA / "sqac" / f"{split}.json").read_text(encoding="utf-8"))
        paragraphs = [p for item in payload["data"] for p in item["paragraphs"]]
        sqac[split] = {
            "paragraphs": len(paragraphs),
            "questions": sum(len(p["qas"]) for p in paragraphs),
            "context_hashes": sorted(
                {hashlib.sha256(p["context"].encode()).hexdigest() for p in paragraphs}
            ),
        }
    overlap = set(sqac["dev"]["context_hashes"]) & set(sqac["test"]["context_hashes"])
    manifest["sqac"] = {**sqac, "dev_test_identical_contexts": len(overlap)}
    counts = Counter()
    passages = set()
    row_count = 0
    fields = set()
    with (DATA / "alia-triplets" / "ALIA-es-legal-administrative-triplets-eval.jsonl").open(
        encoding="utf-8"
    ) as stream:
        for line in stream:
            row = json.loads(line)
            row_count += 1
            fields.update(row)
            counts[str(row["dataset"])] += 1
            passages.add(str(row["id_passage"]))
    manifest["alia_eval"] = {
        "rows": row_count,
        "unique_passage_ids": len(passages),
        "fields": sorted(fields),
        "dataset_counts": dict(counts),
        "human_annotations": False,
        "hard_negatives_in_downloaded_eval": any("negative" in key for key in fields),
    }
    output = ROOT / "docs" / "local-first" / "spanish-data-manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "total_bytes": sum(f["bytes"] for d in manifest["datasets"] for f in d["files"]),
                "sqac": {
                    s: {k: v for k, v in item.items() if k != "context_hashes"}
                    for s, item in sqac.items()
                },
                "alia_eval": manifest["alia_eval"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
