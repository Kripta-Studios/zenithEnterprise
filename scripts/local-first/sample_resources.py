"""Sample the two owned model containers and aggregate GPU use during a local run."""

import argparse
import ctypes
import json
import subprocess
import sys
import time
import urllib.request
from http.client import HTTPException
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--seconds", type=int, default=360)
    parser.add_argument("--container", action="append")
    parser.add_argument("--minimum-free-mib", type=int, default=0)
    parser.add_argument("--ollama-base", choices=["http://127.0.0.1:11436"])
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    containers = args.container or (
        [] if args.ollama_base else ["zenith-lf-cpu-embed-profile", "zenith-lf-cpu-rerank"]
    )
    if any(not name.startswith("zenith-lf-") for name in containers):
        parser.error("resource guard accepts only explicitly owned zenith-lf containers")
    commands = {
        "docker": [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            "{{json .}}",
            *containers,
        ],
        "gpu": [
            "nvidia-smi",
            "--query-gpu=memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
    }
    if not containers:
        commands.pop("docker")
    with args.output.open("w", encoding="utf-8") as stream:
        while time.monotonic() - started < args.seconds:
            sample: dict[str, object] = {"seconds": time.monotonic() - started}
            if sys.platform == "win32":

                class Memory(ctypes.Structure):
                    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                        (name, ctypes.c_ulonglong)
                        for name in (
                            "total",
                            "free",
                            "total_page",
                            "free_page",
                            "total_virtual",
                            "free_virtual",
                            "extended",
                        )
                    ]

                memory = Memory()
                memory.length = ctypes.sizeof(memory)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                    sample["host_free_mib"] = memory.free / 1024**2
                    if args.minimum_free_mib and memory.free < args.minimum_free_mib * 1024**2:
                        sample["resource_abort"] = "host free RAM below configured minimum"
                        for container in containers:
                            subprocess.run(
                                ["docker", "stop", "-t", "1", container], timeout=15, check=False
                            )
                        stream.write(json.dumps(sample) + "\n")
                        stream.flush()
                        break
            for name, command in commands.items():
                try:
                    result = subprocess.run(
                        command, capture_output=True, text=True, encoding="utf-8", timeout=10
                    )
                    sample[name] = {"exit": result.returncode, "output": result.stdout.strip()}
                except subprocess.TimeoutExpired:
                    sample[name] = {"timeout": True}
            if args.ollama_base:
                try:
                    with urllib.request.urlopen(f"{args.ollama_base}/api/ps", timeout=10) as response:
                        sample["ollama"] = json.load(response)
                except (OSError, HTTPException) as exc:
                    sample["ollama"] = {"error": type(exc).__name__}
            stream.write(json.dumps(sample) + "\n")
            stream.flush()
            if args.stop_file is not None and args.stop_file.exists():
                break
            time.sleep(5)


if __name__ == "__main__":
    main()
