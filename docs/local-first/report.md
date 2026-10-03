# Local-first implementation and measured results, 2026-10-01

Current results and publication are in [followup.md](followup.md), including completed
full MCP checks, authorized Jev evaluation, working GPU models and TCP upload readiness.
This file retains the earlier extraction snapshot and its failed attempts.

The subsequent local MCP implementation, cache-inventory correction, executed ingestion
phases and resource-aborted workload are recorded in [continuation.md](continuation.md).
The results below describe the original extraction/baseline snapshot and remain retained.

The two accepted changes are implemented and committed locally, independently from
freshly fetched Martinhdeez main. Focused checks pass. Full suites were executed and
are **not green**: their remaining failures are in unchanged tests. Nothing was pushed,
published, merged, rewritten or closed. The v10 report worktree remains at
7c4af947617d08eecf0f4b9798b033910512d770.

## Exact independent candidates

Common parent: 33b48812c95150348c52d2519159780252c92db2.

| Contribution | Branch | Commit | Tree | Diff |
| --- | --- | --- | --- | --- |
| Old logical upstream #2 | feat/local-judge-contract-standalone | 36f4f7d7155dee047d9eb8f9528de312ba3b59d7 | 839b36ca7075969e9e108d2feaebf611d850bfec | 7 files, +368/-6 |
| Old logical upstream #6 | fix/vite-proxy-prefix-guard-standalone | 9e9bd377dbdad1b3912c4b8aa147c2f8009e7cd2 | e488ce8393928392c8442b540fd79c77e9f646bd | 1 file, +76/-1 |

Worktree paths beneath `C:\Users\Álvaro Schwiedop\Desktop\KriptaStudios\zenithEnterprise-v3-clean`:

- `.scratch\local-judge-contract-standalone`
- `.scratch\vite-proxy-prefix-guard-standalone`
- `.scratch\local-first-baseline` — measurements, public-data manifests, and decision records only.

Judge changed paths: the plan note `.artifacts/to-test/2026-10-01-local-judge-contract.md`,
`backend/app/features/retrieval/judging/{__init__,protocol,tei}.py`, `reranker.py`,
`service.py` and `tests/test_judging.py`. Search actually consumes the contract through
the existing TEI client; it is not an unused interface. It preserves source IDs,
duplicated text, stable ties, batching, cancellation and whole-assessment fallback,
and bounds the sequential request sequence with a total deadline. It adds no provider,
endpoint, schema, dependency or default. The historical increment actually touched twelve
paths; it was inspected and adapted rather than cumulatively cherry-picked.

Proxy changes only `backend/tests/integration/test_proxy_prefixes.py`. It checks the actual
Vite proxy object and variable/literal API targets, missing-prefix failures, intentionally
omitted routes, irrelevant strings and existing Nginx coverage. It is a CI coverage guard.

Neither candidate contains the other, v10, Jev or this benchmark branch.
Draft descriptions, replacement mapping, permission-dependent publication steps and
an unsent Spanish reply are in [pr-drafts.md](pr-drafts.md).

## Actual independent checks

| Gate | Judge | Proxy |
| --- | --- | --- |
| `uv sync --frozen` | Pass, Windows and WSL | Pass, Windows and WSL |
| `uv run ruff check .` / `ruff format --check .` | Pass, exit 0 | Pass, exit 0 |
| `uv run pyright` on Linux | 0 errors, exit 0 | 0 errors, exit 0 |
| Focused real-DB/contract tests | 29 passed, 155.91 s, exit 0 | 7 passed, 34.74 s, exit 0 |
| Complete Linux `uv run python -m pytest -q --tb=short` | 900 passed, 11 skipped, 1 failed; 303.17 s, exit 1 | 885 passed, 11 skipped, 1 failed; 238.14 s, exit 1 |
| `bash scripts/check-licences.sh` | Pass, exit 0 | Pass, exit 0 |
| `npm ci`, `npm run lint`, `npm run build` | Pass, exit 0 each | Pass, exit 0 each |
| Complete Windows `npm run test` | 436 passed, 1 failed; 50.46 s, exit 1 | 436 passed, 1 failed; 264.79 s, exit 1 |
| Actual Vite smoke | Frontend source unchanged | 12 API prefixes proxy JSON; health/docs intentionally serve SPA HTML; exit 0 |

Both full backend runs fail
`tests/integration/test_read_only_checkout.py::test_a_rewritten_file_is_seen_even_at_the_same_length`.
An immediate equal-length rewrite can keep the same observed timestamp. This occurred
on Linux too; it is not only a Windows defect. No assertion was weakened or removed.
The judge frontend fails `uploadQueue.test.ts:138` (expected the delayed item last);
the proxy frontend fails `Analytics.test.tsx:65` (async text lookup times out).
Both frontend trees and failing tests are identical to upstream. They were not changed
or retried to manufacture a green suite. Propose any timing-test repair separately.

Linux full tests used disposable ParadeDB 0.15.26-pg17, application-role RLS and an isolated
cached Python 3.12 runner. The lean container environment omitted offline torch/CUDA wheels;
the eleven dataset/evaluation skips are retained, not reported as quality validation.
Linux type checks instead used the complete cached WSL environment. The final type-checked
source snapshots are hash-linked to each final branch in `verification.json`.

The Windows focused judge run needed UTF-8 mode and a temporary external
WindowsSelectorEventLoopPolicy harness for psycopg. Those are runner adaptations outside
the extraction, not product fixes. Earlier failures include Windows Docker-context decoding,
WSL's missing Docker socket, Docker Desktop host-network access to Ryuk, copied CRLF shell
scripts, and pyright runner prerequisites (Node/libatomic and omitted torch). They remain
recorded. Docker bridge plus `TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal` made the
real-DB run work; canonical LF Git archives made the license script work.

Windows Node was v25.8.1; isolated Vite smoke used cached Node v24.21.0. Upstream Actions
specifies Node 22. These are actual local checks, not a claim that remote Actions ran or
that every local environment exactly reproduces its runner. npm reported thirteen audit
findings on the unchanged lockfile; no unrelated dependency upgrade was bundled.

[verification.json](verification.json) records heads/trees/parents, every captured command,
exit, duration and raw-log SHA-256. Raw evidence stays under `.local-evidence/` and out of
Git. The proxy frontend was observed directly in terminal session 5511; its complete raw
file log was not captured, and the record states that limitation.

## Existing implementation reused

- Uploads already stream in 1 MiB blocks, bound actual received bytes, hash/address storage
  by tenant and clean staging on cancellation. Starlette may spool multipart before the
  handler; do not imply end-to-end network backpressure from a service-level stream.
- Existing SHA deduplication and label protection run before enqueue. New files are queued;
  duplicates return 200 and do not add jobs. Enqueue failure is nonfatal and the existing
  owner CLI requeue scans stranded documents; the benchmark installed the real queue.
- The existing pipeline handles parse, route, chunk, embed, persist and classify/ready.
  PDF page counting and parsing execute synchronously in the async pipeline. That is an
  inspected potential scheduling issue, not a measured dominant stage in this run.
- TEI already plans sequential requests against item/token limits and uses separate query
  timeout and ingestion retry policies. Neither batching nor ingestion was recreated.
- Upstream's GPU Compose override only selects TEI 1.8 images and GPU devices. It does
  **not** set the hardware profile, batch caps or worker concurrency. This differs from
  assumptions about the experimental fork's override.

Effective upstream Compose defaults: server token cap 2,048, client batch cap 4 and worker
process concurrency 1. CPU profile recommends depth 8/ef 100/concurrency 1. GPU profile
recommends tokens 16,384, batch 32, depth 100/ef 200/concurrency 4, but the worker CLI still
defaults to 1 unless its separate environment variable is set. No defaults were raised.

## Measurements and next bottleneck

Hardware: RTX 5070 Ti Laptop, 12,227 MiB VRAM, driver 591.86; about 31.2 GiB physical RAM,
32 logical CPUs. Other applications used about 3.1 GiB VRAM during samples.

Cached miniLM revision 1427fd652930e4ba29e8149678df786c240d8825 was used for both CPU and
GPU attempts, each capped at four CPUs, 2 GiB RAM, 2,048 tokens and client batch four.
CPU image `cpu-1.8` reached health readiness in 13.772 s; max sampled memory was 1.54 GiB.
Six frozen Spanish public fixtures, eight candidates each and two sequential requests per
assessment, returned identical IDs, order and scores through the legacy and typed paths.
Warmed medians: legacy 118.529 ms; typed 121.455 ms. This tiny truncated-text parity fixture
is not a production latency distribution or relevance benchmark.

GPU image `120-1.9` did not reach health readiness in the bounded 180.074 s attempt.
Artifacts were cached; its log reached the Candle backend's model initialization after
weight lookup. Max sampled container memory was about 449 MiB, OOMKilled false. A separate
minimal CUDA driver probe returned cuInit=0 and one device in 0.110 s. Thus GPU model-backend
startup, after successful driver initialization, is the **next measured blocker**. Its root
cause is not yet established. The differing CPU/GPU runtime versions would also confound a
speedup claim even if both had become ready.

Real authenticated multipart upload measurements used public SQAC fixtures, a disposable
database and the application role. Three new uploads returned 201 and pending; their
duplicates returned 200, and exactly three real ingestion jobs existed. See the immutable
per-fixture bytes/hashes and final acknowledgment timings in `verification.json`.
The earlier run observed acknowledgments of 31–63 ms and duplicates about 31 ms. The
final run, after making PDF timestamps/IDs reproducible, observed 265–469 ms and duplicate
acknowledgments of 203–235 ms. All raw runs are retained; this variation is not a percentile
or evidence of a causal regression. These in-process ASGI timings exclude network transfer,
browser behavior and production load. Final upload benchmark: one test passed, 97.84 s
including disposable infrastructure/setup; the acknowledgment counters exclude that setup.

The embedding/reranking endpoint health prerequisite failed. The benchmark therefore did
not dispatch workers or call the query path: upload-to-ready, full phase durations,
event-loop lag, idle/concurrent query percentiles and complete resource peaks remain
**unmeasured**. An earlier simultaneous embedding/reranking startup attempt was stopped
when host memory became tight. No simultaneous embedding/reranking/generation fit is proven.
All owned model services were stopped after measurement; unrelated applications stayed up.

The next smallest performance task is to isolate startup of the single pinned GPU reranker
with the cached supported runtime before changing product profiles. Retain a bounded deadline,
collect CUDA/backend logs and health, and separate runtime/device effects. After readiness,
repeat the existing pipeline benchmark with explicit labels and app-role reads; add phase,
loop-lag and idle/concurrent-search timing. Only then choose a parser offload or batch/worker
change from evidence. No vector DB, distributed quota or agent host is warranted by this run.

## Reproduction and unmet prerequisites

From this measurement worktree, use the installed/cached tools:

```powershell
python scripts/local-first/model_preflight.py zenith-lf-gpu-rerank 18082 --seconds 180
python scripts/local-first/model_preflight.py zenith-lf-cpu-rerank 18083 --seconds 180
../local-judge-contract-standalone/backend/.venv/Scripts/python.exe scripts/local-first/benchmark_rerank.py ../local-judge-contract-standalone .local-data/spanish/sqac/dev.json .local-evidence/models/cpu-parity.json
python scripts/local-first/docker_checks.py ../local-judge-contract-standalone judge .local-evidence/new-run
python scripts/local-first/docker_checks.py ../vite-proxy-prefix-guard-standalone proxy .local-evidence/new-run
```

The named TEI containers, pinned image/weight cache volumes and their caps are recorded
in the measurements; no new weights are required. The Docker checker needs the documented
cached Linux dependency volume, Docker socket and optional cached Node binary. The complete
WSL type checks require its existing full uv environment. Do not use the lean check volume
as a claim of complete offline evaluation dependencies.

For upload-only/queue measurement, point `UV_PROJECT_ENVIRONMENT` at the existing judge
Windows venv, enable `PYTHONUTF8=1`, use the external selector-policy harness via PYTHONPATH,
set `DOCKER_HOST=npipe:////./pipe/dockerDesktopLinuxEngine`, and from `backend` run:

```powershell
$env:ZENITH_RUN_LOCAL_BASELINE='1'
$env:ZENITH_BASELINE_SQAC=(Resolve-Path ../.local-data/spanish/sqac/dev.json).Path
$env:ZENITH_BASELINE_OUTPUT=Join-Path (Resolve-Path ../.local-evidence).Path 'upload/baseline.json'
uv run --no-sync pytest eval/tests/test_local_first_baseline.py -q -s --tb=short
```

To measure readiness rather than only acknowledgment, require both health checks to pass
at 18081/18082 first. The harness reuses existing queue tasks and pipelines at concurrency 1
and has a 300 s drain deadline. Its status trace is groundwork, not full phase/loop/peak
instrumentation. Public fixtures and explicit labels avoid private documents and cloud
classification. Binary-network timing and a simultaneous local generator are later measured
prerequisites, not numbers inferred from these acknowledgments.

## MCP and Spanish evaluation decisions

[mcp-decision.md](mcp-decision.md) proposes an official SDK reference client with an already
cached local Qwen3 4B model, same-machine stdio, current Zenith permissions and authenticated
REST binary uploads. SDK 2.2.0 / protocol 2026-07-28 is a candidate pin; no interop claim is
made. Keycloak is proposed for a later authenticated intranet endpoint. Existing web JWTs
are not a complete MCP OAuth authorization server. No endpoint or IdP was installed.
Interactive host selection, binary-transfer/tool compatibility and simultaneous memory
residency still require concrete tests. Public/private processing destinations stay explicit.

Spanish data: **69,495,568 bytes downloaded**, pinned and hashed. SQAC dev/test covers general
QA; ALIA covers legal/administrative material; MIRACL Spanish topics/qrels are staged without
the large corpus. The synthetic ALIA evaluation contains no hard negatives. The quality
protocol in [spanish-evaluation.md](spanish-evaluation.md) requires held-out document families,
independent relevance judgments and identical candidate panels, and accepts a negative Jev
result. No paid Jev call was made; the supplied key was not used or saved. Spanish superiority
has not been established.
