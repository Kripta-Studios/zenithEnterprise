"""Record each independent checkout's real locked frontend gates without hiding exits."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("label")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    record = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.source)
        .decode()
        .strip(),
        "commands": [],
    }
    for parts in [
        ["npm", "ci"],
        ["npm", "run", "lint"],
        ["npm", "run", "test"],
        ["npm", "run", "build"],
    ]:
        command = " ".join(parts)
        log = args.output / f"{args.label}-{parts[-1]}.log"
        started = time.monotonic()
        with log.open("w", encoding="utf-8") as stream:
            result = subprocess.run(
                command if os.name == "nt" else parts,
                check=False,
                shell=os.name == "nt",
                cwd=args.source / "frontend",
                stdout=stream,
                stderr=subprocess.STDOUT,
            )
        item = {
            "command": command,
            "exit": result.returncode,
            "seconds": round(time.monotonic() - started, 3),
            "log": log.name,
            "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        }
        record["commands"].append(item)
        (args.output / f"{args.label}-frontend.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
        print(json.dumps(item), flush=True)


if __name__ == "__main__":
    main()
