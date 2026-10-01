"""Collect local measurements, exact Git identities and failure-log hashes for review."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / ".local-evidence"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def git(source: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=source).decode().strip()


def main() -> None:
    result: dict = {
        "base": git(ROOT, "rev-parse", "upstream/main"),
        "branches": [],
        "local_check_attempts": [],
        "raw_logs": [],
        "measurements": {},
    }
    for name, directory, snapshot in [
        (
            "feat/local-judge-contract-standalone",
            "local-judge-contract-standalone",
            "final/judge-final-checks.json",
        ),
        (
            "fix/vite-proxy-prefix-guard-standalone",
            "vite-proxy-prefix-guard-standalone",
            "committed-types/proxy-committed-types-checks.json",
        ),
    ]:
        source = ROOT.parent / directory
        manifest = json.loads((EVIDENCE / snapshot).read_text(encoding="utf-8"))
        mismatches = [
            p
            for p, h in manifest["file_sha256"].items()
            if not (source / p).is_file() or digest(source / p) != h
        ]
        assert not mismatches, f"Type-checked snapshot differs from final source: {mismatches}"
        result["branches"].append(
            {
                "name": name,
                "path": str(source),
                "head": git(source, "rev-parse", "HEAD"),
                "tree": git(source, "rev-parse", "HEAD^{tree}"),
                "parent": git(source, "rev-parse", "HEAD^"),
                "changed_paths": git(source, "diff", "--name-only", "upstream/main").splitlines(),
                "status": git(source, "status", "--porcelain"),
                "type_checked_snapshot": snapshot,
                "snapshot_mismatches": mismatches,
            }
        )
    for path in sorted(EVIDENCE.rglob("*checks.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        result["local_check_attempts"].append(
            {
                "manifest": path.relative_to(ROOT).as_posix(),
                "sha256": digest(path),
                "recorded_head": data.get("head"),
                "commands": data["commands"],
                "note": "Pre-commit snapshots record source hashes; see final branch linkage.",
            }
        )
    for path in sorted(EVIDENCE.rglob("*.log")):
        result["raw_logs"].append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )
    for name, relative in [
        ("cpu_startup", "models/zenith-lf-cpu-rerank.json"),
        ("gpu_startup", "models/zenith-lf-gpu-rerank.json"),
        ("cpu_parity", "models/cpu-parity.json"),
        ("upload", "upload/baseline.json"),
        ("vite", "vite-docker/vite-smoke.json"),
        ("judge_frontend", "frontend/judge-frontend.json"),
    ]:
        path = EVIDENCE / relative
        result["measurements"][name] = {
            "source": path.relative_to(ROOT).as_posix(),
            "sha256": digest(path),
            "result": json.loads(path.read_text(encoding="utf-8")),
        }
    result["proxy_frontend_terminal_observation"] = {
        "session": 5511,
        "npm_ci_exit": 0,
        "npm_lint_exit": 0,
        "npm_test_exit": 1,
        "tests_passed": 436,
        "tests_failed": 1,
        "vitest_seconds": 264.79,
        "failure": "src/features/admin/analytics/Analytics.test.tsx:65 findByText(first question)",
        "npm_build_exit": 0,
        "vite_build_seconds": 54.74,
        "note": "Observed directly in terminal output; a complete raw file log was not captured.",
    }
    output = ROOT / "docs/local-first/verification.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "branches": len(result["branches"]),
                "check_attempts": len(result["local_check_attempts"]),
                "raw_logs": len(result["raw_logs"]),
            }
        )
    )


if __name__ == "__main__":
    main()
