"""Run the frozen local admission experiment and monolithic ingestion measurement."""

import argparse
import ctypes
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

from spanish_e2e_runtime import ready


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixture_hash = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    env = {k: v for k, v in os.environ.items() if k not in {"TYPESAFE_API_KEY", "JEV_API_KEY"}}
    env["PYTHONPATH"] = str(Path("backend").resolve())
    env["ZENITH_JWT_SECRET"] = secrets.token_hex(32)
    database = "zenith-lf-gate-db"
    models = set()
    monitors = []

    def save(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def emit(value, **fields):
        record = value if isinstance(value, dict) else {"stage": value, **fields}
        print(json.dumps(record), flush=True)

    def run(command, label):
        with (args.output / (label + ".log")).open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=2100
            )
        if result.returncode:
            raise RuntimeError(f"{label} failed with exit {result.returncode}; retain its log")

    def model_stage(container, kind, port):
        stop = args.output / (kind + ".done")
        handle = (args.output / (kind + "-monitor.log")).open("w", encoding="utf-8")
        monitor = subprocess.Popen(
            [
                str(args.python),
                "scripts/local-first/sample_resources.py",
                str(args.output / (kind + "-resources.jsonl")),
                "--container",
                container,
                "--minimum-free-mib",
                "1536",
                "--seconds",
                "7200",
                "--stop-file",
                str(stop),
            ],
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
        )
        monitors.append((monitor, handle, stop))
        run(["docker", "start", container], "start-" + kind)
        models.add(container)
        save(kind + "-preflight.json", ready(f"http://127.0.0.1:{port}", kind, 900, emit))

    save("run-identity.json", {"fixture_sha256": fixture_hash, "head": head})
    try:

        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong)
                for name in [
                    "total",
                    "free",
                    "total_page",
                    "free_page",
                    "total_virtual",
                    "free_virtual",
                    "extended",
                ]
            ]

        deadline = time.monotonic() + 3600
        stable = 0
        while stable < 6:
            memory = Memory()
            memory.length = ctypes.sizeof(memory)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                raise RuntimeError("cannot inspect available host memory")
            gpu = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,memory.total,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
            )
            used, total, utilization = [int(v.strip()) for v in gpu.splitlines()[0].split(",")]
            free = memory.free / 1024**2
            stable = (
                stable + 1 if free >= 4500 and total - used >= 4500 and utilization <= 85 else 0
            )
            emit(
                {
                    "stage": "waiting_for_resources",
                    "free_ram_mib": round(free),
                    "free_vram_mib": total - used,
                    "stable_samples": stable,
                }
            )
            if time.monotonic() > deadline:
                raise TimeoutError("no available measured GPU window")
            time.sleep(10)
        probe = subprocess.run(
            ["docker", "container", "inspect", database],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if probe.returncode == 0:
            config = json.loads(probe.stdout)[0]
            if config["Config"]["Labels"].get("zenith.gate.fixture") != fixture_hash:
                raise ValueError("dedicated database belongs to another fixture")
            run(["docker", "start", database], "database-start")
        else:
            run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    database,
                    "--network",
                    "zenith-lf-benchmark",
                    "--network-alias",
                    "db-e2e",
                    "--cpus",
                    "2",
                    "--memory",
                    "768m",
                    "--label",
                    "zenith.gate.fixture=" + fixture_hash,
                    "-e",
                    "POSTGRES_USER=test",
                    "-e",
                    "POSTGRES_PASSWORD=test",
                    "-e",
                    "POSTGRES_DB=test",
                    "-v",
                    "zenith-lf-gate-db:/var/lib/postgresql/data",
                    "paradedb/paradedb:0.15.26-pg17",
                    "postgres",
                    "-c",
                    "max_locks_per_transaction=2560",
                ],
                "database-create",
            )
        emit({"stage": "embedding_readiness"})
        model_stage("zenith-lf-e2e-embed", "embed", 18096)
        emit({"stage": "monolithic_upload_and_fresh_retrieval"})
        run(
            [
                sys.executable,
                "scripts/local-first/docker_checks.py",
                ".",
                "gate-capture",
                str(args.output),
                "--test-path",
                "eval/tests/test_spanish_e2e_pipeline.py",
                "--spanish-e2e-panel",
                str(args.fixture),
                "--spanish-e2e-persistent-db",
                "--spanish-e2e-capture-only",
                "--timeout-seconds",
                "1800",
            ],
            "pipeline",
        )
        run(["docker", "stop", "zenith-lf-e2e-embed"], "stop-embed")
        models.remove("zenith-lf-e2e-embed")
        (args.output / "embed.done").touch()
        emit({"stage": "local_reranking_readiness"})
        model_stage("zenith-lf-bge-gpu", "rerank", 18094)
        emit({"stage": "local_scoring"})
        run(
            [
                str(args.python),
                "scripts/local-first/spanish_e2e.py",
                "local",
                "--panel",
                str(args.output / "candidates.json"),
                "--output",
                str(args.output / "bge-scores.json"),
            ],
            "scoring",
        )
        run(
            [
                sys.executable,
                "scripts/local-first/local_gate_validation.py",
                "analyze",
                "--panel",
                str(args.output / "candidates.json"),
                "--scores",
                str(args.output / "bge-scores.json"),
                "--output",
                str(args.output / "local-gate-results.json"),
            ],
            "analysis",
        )
        save("orchestration.json", {"stage": "complete", "paid_calls": 0})
        emit({"stage": "complete", "paid_calls": 0})
    except Exception as exc:
        save("orchestration.json", {"stage": "failed", "error": str(exc)})
        raise
    finally:
        for monitor, handle, stop in monitors:
            stop.touch()
            try:
                monitor.wait(timeout=15)
            except subprocess.TimeoutExpired:
                monitor.terminate()
            handle.close()
        for model in models:
            subprocess.run(["docker", "stop", model], capture_output=True)
        # Only stop a database explicitly created for this frozen fixture.
        probe = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                '{{index .Config.Labels "zenith.gate.fixture"}}',
                database,
            ],
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0 and probe.stdout.strip() == fixture_hash:
            subprocess.run(["docker", "stop", database], capture_output=True)


if __name__ == "__main__":
    main()
