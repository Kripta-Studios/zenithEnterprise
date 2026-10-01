"""Check committed LF sources against a disposable real database using cached tools."""

import argparse
import hashlib
import json
import shlex
import subprocess
import time
from pathlib import Path
from uuid import uuid4


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("label")
    parser.add_argument("output", type=Path)
    parser.add_argument("--focused", action="store_true")
    parser.add_argument("--only", choices=["lint", "types", "tests", "licenses"])
    parser.add_argument("--baseline-fixture", type=Path)
    parser.add_argument("--timeout-seconds", type=float)
    parser.add_argument("--env-volume", default="zenith-lf-check-env-lean")
    parser.add_argument("--test-path", action="append")
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--network")
    parser.add_argument("--public-keycloak-loopback", action="store_true")
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
        "dependency_volume": args.env_volume,
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
    if args.test_path:
        commands = [
            ("tests", "uv run python -m pytest -q --tb=short " + shlex.join(args.test_path))
        ]
    if args.diagnose:
        commands = [
            (label, command + " -vv -o faulthandler_timeout=60" if label == "tests" else command)
            for label, command in commands
        ]
    if args.baseline_fixture:
        commands = [
            (
                "upload-ready",
                "uv run python -m pytest eval/tests/test_local_first_baseline.py -q --tb=short -s",
            )
        ]
    for label, command in commands:
        container = f"zenith-lf-check-{uuid4().hex[:12]}"
        invocation = [
            "docker",
            "run",
            "--rm",
            "--name",
            container,
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
            f"{args.env_volume}:/opt/zenith-env:ro",
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
        if args.network:
            invocation[2:2] = ["--network", args.network]
        if args.public_keycloak_loopback:
            invocation[2:2] = ["-e", "ZENITH_TEST_PUBLIC_KEYCLOAK=1"]
        cached_node = Path(".local-evidence/runner-node/node").resolve()
        if cached_node.exists():
            invocation[2:2] = ["-v", f"{cached_node}:/usr/local/bin/node:ro"]
        if args.baseline_fixture:
            invocation[2:2] = [
                "--network",
                "zenith-lf-benchmark",
                "-v",
                f"{args.baseline_fixture.resolve()}:/public/dev.json:ro",
                "-v",
                f"{args.output.resolve()}:/results",
                "-e",
                "ZENITH_RUN_LOCAL_BASELINE=1",
                "-e",
                "ZENITH_BASELINE_SQAC=/public/dev.json",
                "-e",
                "ZENITH_BASELINE_OUTPUT=/results/upload-ready.json",
                "-e",
                "ZENITH_BASELINE_EMBED=http://embed:80",
                "-e",
                "ZENITH_BASELINE_RERANK=http://rerank:80",
            ]
        started = time.monotonic()
        log = args.output / f"{args.label}-docker-{label}.log"
        with log.open("w", encoding="utf-8") as stream:
            timeout = args.timeout_seconds or (420 if args.baseline_fixture else 900)
            try:
                result = subprocess.run(
                    invocation,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=timeout,
                )
                exit_code = result.returncode
                cleanup = None
            except subprocess.TimeoutExpired:
                exit_code = 124
                # Killing the attached CLI alone leaves the worker container alive.
                # This name belongs solely to the runner created above.
                try:
                    stopped = subprocess.run(
                        ["docker", "rm", "-f", container],
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        timeout=10,
                        check=False,
                    )
                    cleanup = {"container": container, "exit": stopped.returncode}
                except subprocess.TimeoutExpired:
                    cleanup = {"container": container, "error": "cleanup_timeout"}
        record = {
            "command": command,
            "exit": exit_code,
            "timeout_seconds": timeout,
            "cleanup": cleanup,
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
