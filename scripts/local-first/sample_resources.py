"""Sample the two owned model containers and aggregate GPU use during a local run."""

import argparse
import json
import subprocess
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--seconds", type=int, default=360)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    commands = {
        "docker": [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            "{{json .}}",
            "zenith-lf-cpu-embed-profile",
            "zenith-lf-cpu-rerank",
        ],
        "gpu": [
            "nvidia-smi",
            "--query-gpu=memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
    }
    with args.output.open("w", encoding="utf-8") as stream:
        while time.monotonic() - started < args.seconds:
            sample: dict[str, object] = {"seconds": time.monotonic() - started}
            for name, command in commands.items():
                try:
                    result = subprocess.run(
                        command, capture_output=True, text=True, encoding="utf-8", timeout=10
                    )
                    sample[name] = {"exit": result.returncode, "output": result.stdout.strip()}
                except subprocess.TimeoutExpired:
                    sample[name] = {"timeout": True}
            stream.write(json.dumps(sample) + "\n")
            stream.flush()
            if args.stop_file is not None and args.stop_file.exists():
                break
            time.sleep(5)


if __name__ == "__main__":
    main()
