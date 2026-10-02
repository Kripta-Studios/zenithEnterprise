"""Run the fixed public experiment once, waiting for an available local GPU window."""

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from spanish_e2e import digest, save
from spanish_e2e_pairs import combine, prepare


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    call = urllib.request.Request(
        "http://127.0.0.1:11436" + path,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(call, timeout=600) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--nli-model", type=Path, required=True)
    parser.add_argument("--resource-wait-seconds", type=int, default=14400)
    args = parser.parse_args()
    # Never overwrite a failed or completed run. Credentials remain in process memory.
    args.output.mkdir(parents=True, exist_ok=False)
    clean_env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_API_KEY"}
    clean_env["PYTHONPATH"] = str(Path("backend").resolve())
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise ValueError("paid stage requires an ephemeral TYPESAFE_API_KEY environment variable")
    python = str(args.python.resolve())
    processes, handles = [], []
    runner = None
    stage = "waiting_for_resources"

    def start(command, name, paid=False):
        stream = (args.output / (name + ".log")).open("w", encoding="utf-8")
        handles.append(stream)
        process = subprocess.Popen(
            command, stdout=stream, stderr=subprocess.STDOUT, env=os.environ if paid else clean_env
        )
        processes.append(process)
        return process

    def run(command, name, paid=False):
        process = start(command, name, paid)
        if process.wait() != 0:
            raise RuntimeError(f"{name} failed; retained log, no automatic retry")

    def emit(**data):
        save(args.output / "orchestration.json", {"stage": stage, **data})
        print(json.dumps({"stage": stage, **data}), flush=True)

    def owned_container(name, action):
        if name not in {"zenith-lf-e2e-embed", "zenith-lf-bge-gpu"}:
            raise ValueError("container outside this experiment")
        run(["docker", action, name], f"{action}-{name}")

    try:
        deadline, stable = time.monotonic() + args.resource_wait_seconds, 0
        while time.monotonic() < deadline:
            ram = int(
                subprocess.check_output(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "[math]::Floor((Get-CimInstance Win32_OperatingSystem)"
                        ".FreePhysicalMemory/1024)",
                    ],
                    env=clean_env,
                )
                .decode()
                .strip()
            )
            used, total, utilization = map(
                int,
                subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.used,memory.total,utilization.gpu",
                        "--format=csv,noheader,nounits",
                    ],
                    env=clean_env,
                )
                .decode()
                .strip()
                .split(","),
            )
            stable = stable + 1 if ram >= 4500 and total - used >= 7600 and utilization <= 10 else 0
            emit(
                free_ram_mib=ram,
                free_vram_mib=total - used,
                gpu_utilization=utilization,
                stable_samples=stable,
            )
            if stable >= 6:
                break
            time.sleep(10)
        else:
            raise TimeoutError("No available resource window; no paid calls dispatched")
        stage = "upload_and_retrieval"
        owned_container("zenith-lf-e2e-embed", "start")
        health_deadline = time.monotonic() + 180
        while True:
            try:
                with urllib.request.urlopen("http://127.0.0.1:18096/health", timeout=5):
                    break
            except OSError:
                if time.monotonic() > health_deadline:
                    raise TimeoutError("Embedding service not ready") from None
                time.sleep(2)
        prior_completion = args.previous / "completions.jsonl"
        if prior_completion.exists():
            shutil.copyfile(prior_completion, args.output / "completions.jsonl")
        start(
            [
                python,
                "scripts/local-first/sample_resources.py",
                str(args.output / "embed-resources.jsonl"),
                "--container",
                "zenith-lf-e2e-embed",
                "--minimum-free-mib",
                "1024",
                "--seconds",
                "21600",
                "--stop-file",
                str(args.output / "embed.done"),
            ],
            "embedding-monitor",
        )
        runner = start(
            [
                python,
                "scripts/local-first/docker_checks.py",
                ".",
                "spanish-e2e",
                str(args.output),
                "--test-path",
                "eval/tests/test_spanish_e2e_pipeline.py",
                "--spanish-e2e-panel",
                str(args.fixture),
                "--env-volume",
                "zenith-lf-check-env-lean",
                "--timeout-seconds",
                "21600",
            ],
            "pipeline",
        )
        panel = args.output / "candidates.json"
        deadline = time.monotonic() + 3000
        while not panel.exists():
            if runner.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError(
                    "Actual upload/retrieval did not complete; no scoring dispatched"
                )
            time.sleep(5)
        captured = json.loads(panel.read_text(encoding="utf-8"))
        if len(captured["cases"]) != 144 or any(
            len(c["candidates"]) != 32 for c in captured["cases"]
        ):
            raise ValueError("Actual retrieved cohort is incomplete")
        (args.output / "embed.done").touch()
        owned_container("zenith-lf-e2e-embed", "stop")
        stage = "scoring_uncached_pairs"
        emit(panel_sha256=digest(panel))
        for arm in ("bge", "jev"):
            target = args.output / "pair-stages" / arm
            missing = prepare(
                panel,
                args.previous / "candidates.json",
                args.previous / f"{arm}-scores.json",
                target / "plan.json",
                target / "pending-panel.json",
            )
            print(json.dumps({"arm": arm, "uncached_pairs": missing}), flush=True)
        owned_container("zenith-lf-bge-gpu", "start")
        health_deadline = time.monotonic() + 180
        while True:
            try:
                with urllib.request.urlopen("http://127.0.0.1:18094/health", timeout=5):
                    break
            except OSError:
                if time.monotonic() > health_deadline:
                    raise TimeoutError("BGE service not ready") from None
                time.sleep(2)
        paid_dir = args.output / "pair-stages" / "jev"
        paid = start(
            [
                python,
                "scripts/local-first/spanish_e2e.py",
                "jev",
                "--panel",
                str(paid_dir / "pending-panel.json"),
                "--output",
                str(paid_dir / "jev-scores.json"),
                "--ledger",
                str(paid_dir / "jev-ledger.jsonl"),
                "--prior-ledger",
                str(args.previous / "jev-ledger.jsonl"),
                "--public-fixture",
                str(args.fixture),
                "--frozen-criteria",
                str(args.previous / "frozen-jev-criteria.json"),
            ],
            "jev-scoring",
            paid=True,
        )
        local_dir = args.output / "pair-stages" / "bge"
        run(
            [
                python,
                "scripts/local-first/spanish_e2e.py",
                "local",
                "--panel",
                str(local_dir / "pending-panel.json"),
                "--output",
                str(local_dir / "bge-scores.json"),
            ],
            "bge-scoring",
        )
        if paid.wait() != 0:
            raise RuntimeError("Paid stage failed; retained reservations, no retry")
        for arm in ("bge", "jev"):
            target = args.output / "pair-stages" / arm
            combine(
                panel,
                target / "plan.json",
                target / f"{arm}-scores.json",
                args.output / f"{arm}-scores.json",
            )
        owned_container("zenith-lf-bge-gpu", "stop")
        stage = "generator_readiness"
        generator = captured["protocol"]["generator"]
        model = next(m for m in request("/api/tags")["models"] if m["name"] == generator["model"])
        if model["digest"] != generator["model_digest"]:
            raise ValueError("Generator digest changed")
        payload = {
            "model": generator["model"],
            "stream": False,
            "think": False,
            "keep_alive": "15m",
            "messages": [
                {
                    "role": "user",
                    "content": "Responde en español con una frase: ¿cuánto es dos más dos?",
                }
            ],
            "options": {"temperature": 0, "seed": 20261002, "num_ctx": 8192, "num_predict": 256},
        }
        response, residency = request("/api/chat", payload), request("/api/ps")
        resident = next(m for m in residency["models"] if m["name"] == generator["model"])
        if (
            not response.get("done")
            or response.get("done_reason") != "stop"
            or not response["message"]["content"].strip()
        ):
            raise ValueError("Neutral generator probe failed")
        if resident["size"] != resident["size_vram"] or resident["context_length"] != 8192:
            raise ValueError("Generator is not fully resident with the fixed context")
        preflight = args.output / "generator-preflight.json"
        save(
            preflight,
            {"model": model, "request": payload, "response": response, "residency": residency},
        )
        start(
            [
                python,
                "scripts/local-first/sample_resources.py",
                str(args.output / "generation-resources.jsonl"),
                "--ollama-base",
                "http://127.0.0.1:11436",
                "--seconds",
                "21600",
                "--stop-file",
                str(args.output / "generation.done"),
            ],
            "generation-monitor",
        )
        stage = "actual_paired_queries"
        save(
            args.output / "models-ready.json",
            {
                "ready": True,
                "panel_sha256": digest(panel),
                "generator_digest": model["digest"],
                "preflight_sha256": digest(preflight),
            },
        )
        emit()
        if runner.wait() != 0:
            raise RuntimeError("Actual paired query/audit run failed")
        checks = json.loads((args.output / "spanish-e2e-docker-checks.json").read_text())
        results = json.loads((args.output / "generated-results.json").read_text())
        if any(c["exit"] for c in checks["commands"]):
            raise RuntimeError("Actual integration test failed despite helper process exit")
        if results["phase"] != "complete" or len(results["cases"]) != 128:
            raise RuntimeError("Actual paired cohort is incomplete")
        request(
            "/api/chat",
            {"model": generator["model"], "messages": [], "stream": False, "keep_alive": 0},
        )
        stage = "independent_entailment"
        emit()
        run(
            [
                python,
                "-m",
                "eval.spanish_e2e_nli",
                "--results",
                str(args.output / "generated-results.json"),
                "--model",
                str(args.nli_model),
                "--output",
                str(args.output / "independently-graded.json"),
            ],
            "nli",
        )
        stage = "complete"
        emit(summary_sha256=digest(args.output / "e2e-summary.json"))
    except Exception as error:
        emit(error_type=type(error).__name__, reason=str(error))
        raise
    finally:
        for name in ("embed.done", "generation.done"):
            (args.output / name).touch()
        if runner is not None and runner.poll() is None:
            # Match this unique evidence bind mount and test command before stopping.
            # Other checks, Docker applications and host training processes stay untouched.
            names = (
                subprocess.check_output(
                    ["docker", "ps", "--filter", "name=zenith-lf-check-", "--format", "{{.Names}}"],
                    env=clean_env,
                )
                .decode()
                .splitlines()
            )
            expected = str(args.output.resolve()).replace("\\", "/").casefold()
            for name in names:
                config = json.loads(subprocess.check_output(["docker", "inspect", name]))[0]
                bound = any(
                    m["Source"].replace("\\", "/").casefold() == expected
                    and m["Destination"] == "/results"
                    for m in config["Mounts"]
                )
                if bound and "test_spanish_e2e_pipeline" in " ".join(config["Config"]["Cmd"]):
                    subprocess.run(
                        ["docker", "stop", "--timeout", "10", name], env=clean_env, check=True
                    )
            runner.wait(timeout=60)
        for stream in handles:
            stream.close()


if __name__ == "__main__":
    main()
