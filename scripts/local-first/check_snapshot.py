"""Run exact independent source snapshots through Linux CI commands; no remote writes."""

import argparse
import hashlib
import json
import subprocess
import tarfile
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("label")
    parser.add_argument("output", type=Path)
    parser.add_argument("--only", choices=["types"])
    parser.add_argument("--cached-env")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    names = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=args.source,
        )
        .decode()
        .split("\0")
    )
    archive = args.output / f"{args.label}.tar"
    hashes = {}
    with tarfile.open(archive, "w") as tar:
        for name in sorted(filter(None, names)):
            path = args.source / name
            if path.is_file():
                tar.add(path, arcname=name)
                hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    destination = f"/home/alvaro/zenith-local-first-20261001/{args.label}"
    drive = archive.resolve().drive[0].lower()
    linux_archive = f"/mnt/{drive}/" + archive.resolve().as_posix()[3:]
    # These are local task-owned paths. Quote them before placing them in shell code.
    import shlex

    setup = (
        f"mkdir -p {shlex.quote(destination)}; "
        f"tar -xf {shlex.quote(linux_archive)} -C {shlex.quote(destination)}"
    )
    subprocess.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-c", setup], check=True)
    commands = [
        ("sync", "cd backend && uv sync --frozen"),
        ("lint", "cd backend && uv run ruff check ."),
        ("format", "cd backend && uv run ruff format --check ."),
        ("types", "cd backend && uv run pyright"),
        ("tests", "cd backend && uv run pytest -q"),
        ("licenses", "bash scripts/check-licences.sh"),
        ("web-install", "cd frontend && npm ci"),
        ("web-types", "cd frontend && npm run lint"),
        ("web-tests", "cd frontend && npm run test"),
        ("web-build", "cd frontend && npm run build"),
    ]
    if args.only:
        commands = [(name, command) for name, command in commands if name == args.only]
    manifest = {
        "label": args.label,
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.source)
        .decode()
        .strip(),
        "file_sha256": hashes,
        "commands": [],
    }
    for name, command in commands:
        script = (
            "export PATH=/home/alvaro/zenith-v10-tools/bin:/usr/local/bin:/usr/bin:/bin:"
            "/mnt/wsl/docker-desktop/cli-tools/usr/bin; "
            "export DOCKER_HOST=unix:///var/run/docker.sock; "
            + (
                f"export UV_PROJECT_ENVIRONMENT={shlex.quote(args.cached_env)}; "
                if args.cached_env
                else ""
            )
            + f"cd {shlex.quote(destination)}; {command}"
        )
        started = time.monotonic()
        log = args.output / f"{args.label}-{name}.log"
        with log.open("w", encoding="utf-8") as stream:
            result = subprocess.run(
                ["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-c", script],
                check=False,
                stdout=stream,
                stderr=subprocess.STDOUT,
            )
        record = {
            "command": command,
            "exit": result.returncode,
            "seconds": round(time.monotonic() - started, 3),
            "log": log.name,
            "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        }
        manifest["commands"].append(record)
        (args.output / f"{args.label}-checks.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        print(json.dumps(record), flush=True)
        if name == "sync" and result.returncode:
            break


if __name__ == "__main__":
    main()
