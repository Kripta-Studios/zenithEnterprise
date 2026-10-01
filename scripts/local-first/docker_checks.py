"""Check committed LF sources against a disposable real database using cached tools."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("label")
    parser.add_argument("output", type=Path)
    parser.add_argument("--focused", action="store_true")
    parser.add_argument("--only", choices=["lint", "types", "tests", "licenses"])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.source).decode().strip()
    tree = (
        subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=args.source)
        .decode()
        .strip()
    )
    archive = (args.output / f"{args.label}-committed.tar").resolve()
    subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "archive",
            "--format=tar",
            f"--output={archive}",
            head,
        ],
        cwd=args.source,
        check=True,
    )
    image = (
        subprocess.check_output(
            ["docker", "image", "inspect", "trace-it-backend:ci", "--format", "{{.Id}}"]
        )
        .decode()
        .strip()
    )
    setup = (
        "ln -s /usr/local/bin/python3.12 /usr/bin/python3.12; "
        "mkdir -p /home/alvaro/zenith-local-first-20261001/proxy-final/backend /workspace; "
        "ln -s /opt/zenith-env /home/alvaro/zenith-local-first-20261001/proxy-final/backend/.venv; "
        "tar -xf /source.tar -C /workspace; cd /workspace/backend; "
    )
    records = {
        "head": head,
        "tree": tree,
        "runner_image": image,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "excluded_offline_wheels": ["torch", "nvidia", "triton"],
        "commands": [],
    }
    commands = [
        ("lint", "uv run ruff check . && uv run ruff format --check ."),
        ("types", "uv run pyright"),
        ("tests", "uv run python -m pytest -q --tb=short"),
        ("licenses", "cd /workspace && bash scripts/check-licences.sh"),
    ]
    if args.focused:
        commands = [
            (
                "focused",
                "uv run python -m pytest app/features/retrieval/tests/test_rerank.py -q --tb=short",
            )
        ]
    if args.only:
        commands = [(label, command) for label, command in commands if label == args.only]
    for label, command in commands:
        invocation = [
            "docker",
            "run",
            "--rm",
            "--user",
            "0",
            "--cpus",
            "4",
            "--memory",
            "3g",
            "--entrypoint",
            "sh",
            "-v",
            f"{archive}:/source.tar:ro",
            "-v",
            "zenith-lf-check-env-lean:/opt/zenith-env:ro",
            "-v",
            "/var/run/docker.sock:/var/run/docker.sock",
            "-e",
            "UV_PROJECT_ENVIRONMENT=/opt/zenith-env",
            "-e",
            "UV_NO_SYNC=1",
            "-e",
            "PYTHONPATH=/workspace/backend",
            "-e",
            "DOCKER_HOST=unix:///var/run/docker.sock",
            "-e",
            "TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal",
            image,
            "-c",
            setup + command,
        ]
        # An existing cached official Node binary avoids pyright's automatic Node download.
        cached_node = Path(".local-evidence/runner-node/node").resolve()
        if cached_node.exists():
            invocation[2:2] = ["-v", f"{cached_node}:/usr/local/bin/node:ro"]
        started = time.monotonic()
        log = args.output / f"{args.label}-docker-{label}.log"
        with log.open("w", encoding="utf-8") as stream:
            result = subprocess.run(
                invocation, stdout=stream, stderr=subprocess.STDOUT, check=False
            )
        record = {
            "command": command,
            "exit": result.returncode,
            "seconds": round(time.monotonic() - started, 3),
            "log": log.name,
            "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        }
        records["commands"].append(record)
        (args.output / f"{args.label}-docker-checks.json").write_text(
            json.dumps(records, indent=2), encoding="utf-8"
        )
        print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
