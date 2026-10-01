"""Measure readiness and residency of existing cached services, with a bounded wait."""

import argparse
import json
import subprocess
import time
import urllib.request
from http.client import HTTPException
from pathlib import Path


def command(*args: str) -> str:
    return subprocess.check_output(args, text=True, encoding="utf-8", errors="replace").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("container")
    parser.add_argument("port", type=int)
    parser.add_argument("--seconds", type=int, default=180)
    parser.add_argument("--output", type=Path, default=Path(".local-evidence/models"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    inspect = json.loads(command("docker", "inspect", args.container))[0]
    record = {
        "container": args.container,
        "image": inspect["Image"],
        "args": inspect["Config"]["Cmd"],
        "memory_limit": inspect["HostConfig"]["Memory"],
        "cpu_limit": inspect["HostConfig"]["NanoCpus"],
        "samples": [],
        "ready": False,
    }
    command("docker", "start", args.container)
    while time.monotonic() - started < args.seconds:
        sample = {"seconds": round(time.monotonic() - started, 3)}
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{args.port}/health", timeout=2
            ) as response:
                record["ready"] = response.status == 200
        except (OSError, HTTPException) as exc:
            sample["health_error"] = type(exc).__name__
        sample["stats"] = command(
            "docker", "stats", "--no-stream", "--format", "{{json .}}", args.container
        )
        sample["gpu"] = command(
            "nvidia-smi",
            "--query-gpu=memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        )
        record["samples"].append(sample)
        print(json.dumps(sample), flush=True)
        if record["ready"]:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{args.port}/info", timeout=5
            ) as response:
                record["info"] = json.load(response)
            break
        time.sleep(10)
    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    record["state"] = json.loads(command("docker", "inspect", args.container))[0]["State"]
    logs = subprocess.run(
        ["docker", "logs", args.container],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (args.output / f"{args.container}.log").write_text(logs.stdout + logs.stderr, encoding="utf-8")
    (args.output / f"{args.container}.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    print(
        json.dumps({"ready": record["ready"], "elapsed_seconds": record["elapsed_seconds"]}),
        flush=True,
    )
    if not record["ready"]:
        command("docker", "stop", args.container)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
