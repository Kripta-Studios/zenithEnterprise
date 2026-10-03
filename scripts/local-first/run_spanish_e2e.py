"""Run the fixed public experiment once, waiting for an available local GPU window."""

import argparse
import getpass
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from spanish_e2e import digest, save
from spanish_e2e_pairs import combine, prepare
from spanish_e2e_runtime import completed_scores, load_json, ready


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
    parser.add_argument("--maximum-background-gpu-utilization", type=int, default=10)
    parser.add_argument("--minimum-free-vram-mib", type=int, default=6500)
    parser.add_argument("--minimum-free-ram-mib", type=int, default=4500)
    parser.add_argument("--model-readiness-seconds", type=int, default=900)
    parser.add_argument("--allow-partial-gpu-generator", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--credential-stdin", action="store_true")
    parser.add_argument("--reuse-public-capture", action="store_true")
    parser.add_argument("--cached-scores-only", action="store_true")
    args = parser.parse_args()
    if args.credential_stdin:
        os.environ["TYPESAFE_API_KEY"] = getpass.getpass(
            "Approved public research key (not echoed): "
        )
    # Never overwrite a failed or completed run. Credentials remain in process memory.
    args.output.mkdir(parents=True, exist_ok=args.resume)
    binding = {"fixture_sha256": digest(args.fixture), "source_run": str(args.previous.resolve())}
    identity_path = args.output / "run-identity.json"
    if identity_path.exists():
        if load_json(identity_path) != binding:
            raise ValueError("resume belongs to another fixture or source run")
    elif args.resume:
        raise ValueError("resume requires an existing bound run")
    else:
        save(identity_path, binding)
    attempt = args.output / "attempts" / str(time.time_ns())
    attempt.mkdir(parents=True)
    for name in (
        "orchestration.json",
        "models-ready.json",
        "spanish-e2e-docker-checks.json",
        "embed-resources.jsonl",
        "generation-resources.jsonl",
        "generated-results.json",
        "progress.json",
    ):
        source = args.output / name
        if source.exists():
            shutil.copyfile(source, attempt / name)
    for name in ("models-ready.json", "capture-ready.json", "embed.done", "generation.done"):
        (args.output / name).unlink(missing_ok=True)
    clean_env = {k: v for k, v in os.environ.items() if k not in {"TYPESAFE_API_KEY", "JEV_API_KEY"}}
    clean_env["PYTHONPATH"] = str(Path("backend").resolve())
    python = str(args.python.resolve())
    processes, handles = [], []
    runner = None
    owned_models = set()
    database_owned = False
    owned_generator = None
    stage = "waiting_for_resources"

    def start(command, name, paid=False):
        stream = (attempt / (name + ".log")).open("w", encoding="utf-8")
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
        save(attempt / "orchestration.json", {"stage": stage, **data})
        print(json.dumps({"stage": stage, **data}), flush=True)

    def owned_container(name, action):
        if name not in {"zenith-lf-e2e-embed", "zenith-lf-bge-gpu"}:
            raise ValueError("container outside this experiment")
        if action == "start":
            owned_models.add(name)
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
            stable = (
                stable + 1
                if (
                    ram >= args.minimum_free_ram_mib
                    and total - used >= args.minimum_free_vram_mib
                    and utilization <= args.maximum_background_gpu_utilization
                )
                else 0
            )
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
        emit()
        database = "zenith-lf-e2e-db"
        probe = subprocess.run(["docker", "inspect", database], capture_output=True, env=clean_env)
        database_identity = digest(identity_path)
        if args.reuse_public_capture:
            source_identity = args.previous / "run-identity.json"
            if load_json(source_identity)["fixture_sha256"] != digest(args.fixture):
                raise ValueError("public capture belongs to another frozen fixture")
            if probe.returncode:
                raise ValueError("capture reuse requires its existing isolated database")
            database_identity = digest(source_identity)
            for name in ("account.json", "candidates.json", "upload-first.json"):
                source = args.previous / name
                target = args.output / name
                if target.exists() and target.read_bytes() != source.read_bytes():
                    raise ValueError("capture reuse target differs from its bound source")
                shutil.copyfile(source, target)
            shutil.copytree(
                args.previous / "public-documents", args.output / "public-documents", dirs_exist_ok=True
            )
        if probe.returncode:
            run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    database,
                    "--label",
                    "zenith.e2e.identity=" + database_identity,
                    "--network",
                    "zenith-lf-benchmark",
                    "--network-alias",
                    "db-e2e",
                    "--memory",
                    "768m",
                    "--cpus",
                    "2",
                    "-v",
                    "zenith-lf-e2e-db:/var/lib/postgresql/data",
                    "-e",
                    "POSTGRES_USER=test",
                    "-e",
                    "POSTGRES_PASSWORD=test",
                    "-e",
                    "POSTGRES_DB=test",
                    "paradedb/paradedb:0.15.26-pg17",
                    "postgres",
                    "-c",
                    "max_locks_per_transaction=2560",
                ],
                "database-create",
            )
        else:
            config = json.loads(probe.stdout)[0]
            if config["Config"]["Labels"].get("zenith.e2e.identity") != database_identity:
                raise ValueError("existing database belongs to another evaluation run")
            run(["docker", "start", database], "database-start")
        database_owned = True
        prior_completion = args.previous / "completions.jsonl"
        if prior_completion.exists() and not (args.output / "completions.jsonl").exists():
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
        if not (args.output / "candidates.json").exists():
            owned_container("zenith-lf-e2e-embed", "start")
            save(
                args.output / "embed-preflight.json",
                ready("http://127.0.0.1:18096", "embed", args.model_readiness_seconds, emit),
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
                "--spanish-e2e-persistent-db",
                "--env-volume",
                "zenith-lf-check-env-lean",
                "--timeout-seconds",
                "21600",
            ],
            "pipeline",
        )
        panel = args.output / "candidates.json"
        deadline = time.monotonic() + 3000
        while not (args.output / "capture-ready.json").exists():
            if runner.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError(
                    "Actual upload/retrieval did not complete; no scoring dispatched"
                )
            time.sleep(5)
        captured = load_json(panel)
        if len(captured["cases"]) != 144 or any(
            len(c["candidates"]) != 32 for c in captured["cases"]
        ):
            raise ValueError("Actual retrieved cohort is incomplete")
        (args.output / "embed.done").touch()
        if "zenith-lf-e2e-embed" in owned_models:
            owned_container("zenith-lf-e2e-embed", "stop")
        stage = "scoring_uncached_pairs"
        emit(panel_sha256=digest(panel))
        missing_by_arm = {}
        reused_stage = completed_scores(panel, args.output)
        for arm in ("bge", "jev"):
            if reused_stage:
                missing_by_arm[arm] = 0
                print(json.dumps({"arm": arm, "reused_completed_stage": True}), flush=True)
                continue
            target = args.output / "pair-stages" / arm
            missing = prepare(
                panel,
                args.previous / "candidates.json",
                args.previous / f"{arm}-scores.json",
                target / "plan.json",
                target / "pending-panel.json",
            )
            print(json.dumps({"arm": arm, "uncached_pairs": missing}), flush=True)
            missing_by_arm[arm] = missing
            if missing == 0:
                original = load_json(args.previous / f"{arm}-scores.json")
                save(
                    target / f"{arm}-scores.json",
                    {
                        **original,
                        "panel_sha256": digest(target / "pending-panel.json"),
                        "queries": {qid: {"scores": []} for qid in original["queries"]},
                        "new_calls": 0,
                        "new_dollars": 0,
                    },
                )
        if missing_by_arm["jev"] and not os.environ.get("TYPESAFE_API_KEY"):
            raise ValueError("uncached paid pairs require the authorized ephemeral credential")
        if args.cached_scores_only and any(missing_by_arm.values()):
            raise ValueError("repeat requires exact cached scores; no new provider calls allowed")
        if missing_by_arm["bge"]:
            owned_container("zenith-lf-bge-gpu", "start")
            save(
                args.output / "bge-preflight.json",
                ready("http://127.0.0.1:18094", "rerank", args.model_readiness_seconds, emit),
            )
        paid_dir = args.output / "pair-stages" / "jev"
        paid = (
            start(
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
            if missing_by_arm["jev"]
            else None
        )
        local_dir = args.output / "pair-stages" / "bge"
        if missing_by_arm["bge"]:
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
        if paid is not None and paid.wait() != 0:
            raise RuntimeError("Paid stage failed; retained reservations, no retry")
        for arm in ("bge", "jev"):
            if reused_stage:
                continue
            target = args.output / "pair-stages" / arm
            combine(
                panel,
                target / "plan.json",
                target / f"{arm}-scores.json",
                args.output / f"{arm}-scores.json",
            )
        if "zenith-lf-bge-gpu" in owned_models:
            owned_container("zenith-lf-bge-gpu", "stop")
        stage = "generator_readiness"
        emit()
        start(
            [
                python,
                "scripts/local-first/sample_resources.py",
                str(args.output / "generation-resources.jsonl"),
                "--ollama-base",
                "http://127.0.0.1:11436",
                "--seconds",
                "21600",
                "--minimum-free-mib",
                "1024",
                "--stop-file",
                str(args.output / "generation.done"),
            ],
            "generation-monitor",
        )
        generator = captured["protocol"]["generator"]
        model = next(m for m in request("/api/tags")["models"] if m["name"] == generator["model"])
        if model["digest"] != generator["model_digest"]:
            raise ValueError("Generator digest changed")
        owned_generator = generator["model"]
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
        if resident["context_length"] != 8192:
            raise ValueError("Generator context differs from the frozen protocol")
        if resident["size"] != resident["size_vram"] and not args.allow_partial_gpu_generator:
            raise ValueError(
                "Generator is not fully resident; explicit shared-hardware option required"
            )
        preflight = args.output / "generator-preflight.json"
        save(
            preflight,
            {"model": model, "request": payload, "response": response, "residency": residency},
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
        while runner.poll() is None:
            resource_path = args.output / "generation-resources.jsonl"
            if resource_path.exists():
                samples = resource_path.read_text(encoding="utf-8").splitlines()
                if samples and json.loads(samples[-1]).get("resource_abort"):
                    raise RuntimeError(
                        "Generation interrupted by owned resource guard; resume retained"
                    )
            time.sleep(5)
        if runner.returncode != 0:
            raise RuntimeError("Actual paired query/audit run failed")
        checks = load_json(args.output / "spanish-e2e-docker-checks.json")
        results = load_json(args.output / "generated-results.json")
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
        run(["docker", "stop", database], "database-stop-before-nli")
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
        for name in owned_models:
            subprocess.run(
                ["docker", "stop", "--timeout", "10", name], env=clean_env, timeout=30, check=False
            )
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
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=30)
        if database_owned:
            subprocess.run(
                ["docker", "stop", "--timeout", "10", "zenith-lf-e2e-db"],
                env=clean_env,
                timeout=30,
                check=False,
            )
        if owned_generator is not None:
            unload = urllib.request.Request(
                "http://127.0.0.1:11436/api/generate",
                data=json.dumps({"model": owned_generator, "keep_alive": 0}).encode(),
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(unload, timeout=30):
                    pass
            except OSError:
                pass
        for stream in handles:
            stream.close()


if __name__ == "__main__":
    main()
