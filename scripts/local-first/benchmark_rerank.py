"""Check legacy/typed TEI parity on one frozen public Spanish workload, without Jev."""

import argparse
import asyncio
import hashlib
import json
import os
import secrets
import statistics
import subprocess
import sys
import time
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


async def run(args: argparse.Namespace) -> None:
    head = (
        (
            await asyncio.to_thread(
                subprocess.check_output, ["git", "rev-parse", "HEAD"], cwd=args.source
            )
        )
        .decode()
        .strip()
    )
    sys.path.insert(0, str((args.source / "backend").resolve()))
    os.environ.setdefault("ZENITH_JWT_SECRET", secrets.token_hex(32))
    from app.core.hardware import PROFILES
    from app.features.retrieval.judging.protocol import Candidate
    from app.features.retrieval.judging.tei import TeiJudge
    from app.features.retrieval.reranker import TeiReranker

    data = json.loads(args.fixture.read_text(encoding="utf-8"))
    paragraphs = [p for item in data["data"] for p in item["paragraphs"]]
    # A transport/parity fixture, not a relevance benchmark: truncation may remove answers.
    candidates = [
        Candidate(uuid5(NAMESPACE_URL, p["context"]), p["context"][:500]) for p in paragraphs[:8]
    ]
    questions = [p["qas"][0]["question"] for p in paragraphs[:6]]
    reranker = TeiReranker(url=args.url, profile=PROFILES["cpu"])
    judge = TeiJudge(reranker)
    await reranker.rank(questions[0], [c.text for c in candidates])
    records = []
    for question in questions:
        started = time.perf_counter()
        legacy = await reranker.rank(question, [c.text for c in candidates])
        legacy_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        batch = await judge.assess(question, candidates)
        typed_ms = (time.perf_counter() - started) * 1000
        expected = [(str(candidates[s.index].id), s.score) for s in legacy]
        actual = [(str(s.candidate_id), s.rank_value) for s in batch.judgments]
        records.append(
            {
                "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
                "legacy_ms": legacy_ms,
                "typed_ms": typed_ms,
                "identical": expected == actual,
                "legacy": expected,
                "typed": actual,
            }
        )
    output = {
        "head": head,
        "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
        "endpoint": args.url,
        "candidates": 8,
        "client_batch_size": 4,
        "candidate_text_sha256": [hashlib.sha256(c.text.encode()).hexdigest() for c in candidates],
        "warmup_calls": 1,
        "requests_per_assessment": 2,
        "records": records,
        "legacy_median_ms": statistics.median(r["legacy_ms"] for r in records),
        "typed_median_ms": statistics.median(r["typed_ms"] for r in records),
        "quality_claim": False,
        "provider_calls": {"local_tei_assessments": 13, "local_tei_http_requests": 26, "jev": 0},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {k: v for k, v in output.items() if k not in {"records", "candidate_text_sha256"}}
        )
    )
    if not all(r["identical"] for r in records):
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:18083")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
