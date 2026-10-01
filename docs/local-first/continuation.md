# Continuation: local MCP and measured ingestion

This supplements the original report; its failures remain part of the evidence.
No branch was pushed, remote PR changed, main moved, model weights downloaded or paid
Jev inference started. Both accepted extractions still start independently at freshly
verified upstream main `33b48812c95150348c52d2519159780252c92db2`:

| Branch | Commit | Independent focused result |
| --- | --- | --- |
| `feat/local-judge-contract-standalone` | `36f4f7d7155dee047d9eb8f9528de312ba3b59d7` | 29 passed, 155.91 s |
| `fix/vite-proxy-prefix-guard-standalone` | `9e9bd377dbdad1b3912c4b8aa147c2f8009e7cd2` | 7 passed, 34.74 s |

Their full backend/frontend failures and Vite smoke are in the original
[report](report.md), [verification](verification.json) and [PR drafts](pr-drafts.md).
They are not claimed fully green. The 15 original upstream PRs remain open.

## Optional local MCP

Independent branch `feat/local-mcp-stdio`, commit
`5f590bb3f1ca24e4e20dafb2ee995636ab25f7eb`, tree
`75a4d412ce78a591866242f429796898aebda6f8`, based on the same upstream main,
implements the local proof authorized by “continue, do it all.” It contains neither
accepted extraction nor v10/Jev. See its `docs/local-mcp.md` for runnable commands.

The official SDK is pinned to optional extra `mcp==2.2.0`; the dev group includes it
for CI checks. No pre-existing locked package version changed. There is no HTTP MCP
listener, authorization service or product-default change. Tools provide bounded search,
original source fragments and document metadata/status, under current user permissions
and application-role RLS. Search/source explicitly reuse the existing permission guard;
each operation resolves current authorization. Source visibility is rechecked after
inference and before returning citations. The local adapter checks token version on
every operation; REST's stateless expiry behavior is unchanged.
The SDK lifespan requires the application role before any customer read and calls the
existing RLS startup guard. An owner/platform connection is rejected even on an empty
database. Startup is bounded to 30 seconds; the reference client uses 35 seconds.

The trusted upload host sends an explicitly selected, bounded regular file to existing
authenticated multipart REST with labels; 201/pending, 200/deduplicated and 403 after
permission revocation are tested. Upload is not a model-facing filesystem tool, and
pending is not ready. This proof uses ASGI transport for REST; a complete interactive
desktop host/binary-network integration remains unverified.

Actual SDK calls negotiate protocol `2026-07-28`; tests include a real stdio subprocess,
tenant/label isolation, forged scope, token expiry/type/version, revocation during search,
cancellation, bounds, source coordinates and safe errors. First 14 assertions passed but
seven SDK fixture teardown errors exposed an invalid cross-task fixture lifecycle. The
corrected run passed 14 in 32.10 s. Expanded upload run passed 22 in 362.22 s under load.
Final completion/source-revocation tests and complete backend results are recorded in
`continuation-verification.json`; the opt-in real-model test is skipped in normal CI.
Final Linux focused checks at the recorded final head: **29 passed, one skipped in
203.96 seconds**, Docker exit **0** (227.016 s including runner/setup). This includes
the actual stdio subprocess and real owner-role rejection. The initial guard extraction
passed 28 but failed stdio initialize at its former ten-second test budget; the failed
216.43-second run is retained. The revised test matches the real reference host budget,
and startup itself now has a hard 30-second limit. Async engine disposal in the new
owner-role test was corrected to avoid the test's synchronous-close warnings.

The Windows full suite was operator-aborted after **803.598 seconds** without completion;
its empty output log and metadata are retained. A separate diagnostic focused Windows
run eventually passed **28 with one skip in 177.82 s**, after a migration subprocess pipe
wait. This identifies where the wait occurred, not its root cause. The first Linux full
suite reached the **600-second** external deadline, exit **124**, owned-container removal
exit **0**, elapsed **602.625 s**; this is an incomplete suite, not a green check. The
longer complete Linux run tests initial MCP implementation commit
`7007adcfb46ad0a8ff8fc3368bf4d2e4a82dc74d`; the final startup delta is covered separately
by the 29 focused tests. Its exact full-suite outcome is recorded below and in the JSON.
The longer run also reached its external deadline: **exit 124 after 1803.329 s**,
owned-container removal **0**, approximately 93% through the suite. It passed both
migration round trips and model/schema verification before reaching profile API tests.
It did not finish and supplies no full-suite green result. The remaining integration
paths were run separately against the final guarded commit; those results and exact
coverage are recorded in the JSON. This is explicit split coverage across snapshots,
not a completed single CI run.
The remaining paths passed **64 tests in 262.91 s**, Docker exit **0** (288.484 s
including runner/setup), on the final guarded head. The final Linux collection contains
**923 cases**. Reconciliation accounts for all of them: **911 observed passing outcomes
and 12 skips**, across the partial original full run, completed final MCP checks and
completed final integration tail. Only three UUIDs generated dynamically in the system
API refusal test IDs were normalized; method/action/body remain distinct and every raw
ID is retained. This verifies coverage, not completion of a whole-session teardown or
a single passing CI run. The earlier extraction failures remain recorded; the unchanged
checkout test passed in this later tail and was not patched or hidden through retries.

The cached Qwen3 tag had an unconditional `<think>` template. The initial test passed
citation identity while its 256-token answer was unfinished; that result is explicitly
**not a usable answer proof**. With a completion gate and `/no_think`, the test failed
and the response was correctly withheld. Both artifacts are retained. No model cache
template was modified to conceal this failure.

The already cached Llama3.2 3B Q4_K_M tag then returned **“Treinta días. [1]”**, finishing
normally in **3.203 seconds**, including MCP reauthorization, with Ollama total duration
3.0382768 s. The actual integration test passed in **18.57 seconds** including disposable
setup. Tag/manifest digest:
`a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`;
all six declared blobs' sizes and hashes were verified, total 2,019,393,189 bytes.
This is one already seeded public source with original page/character coordinates,
not an upload-to-ready proof, semantic citation audit or Spanish quality comparison.
The Llama weights are not shipped; their separate model license applies.
The final guarded commit was tested again: **one passed in 141.75 seconds** including
slow disposable migration setup. It returned the same grounded answer with normal
completion; host generation/reauthorization took **18.469 s**, Ollama total **16.9322411 s**.
Both runs are retained. The differing single-run durations under concurrent checks do
not define a performance distribution or a causal slowdown. The final owned proof
server was stopped after the test.

Ollama 0.34.3 ran solely on loopback, cloud disabled, parallelism one, one loaded model,
4096 context, 256 output budget and keep-alive zero. The fixed host sends at most three
1,000-character sources, never pulls weights, bypasses environment proxies and redirects,
and withholds incomplete answers or changed/revoked citations. Its child receives a
restricted local configuration environment. The owned local server was stopped afterward.
This proves a local client/model path, not simultaneous embed/rerank/generator memory fit.

## Ingestion actually executed

Measurement commit `1c2beae4dc44dbb853aab1452843d123e772ac77`, tree
`01de74dc8c550226f57b4e20f9886bd993785233`, added benchmark-only stage clocks. It reused
the real upload/queue/pipeline/parser/chunker/embedding batcher/persistence; no ingestion
product path was recreated. Effective worker concurrency was **one**, CPU profile,
query limit **eight**, one serial query at a time scoped to the first ready file.
Public SQAC fixture hashes, resource samples and exact commands are in raw JSON.

A correction to the earlier cache inventory: `zenith-v3-tei-cpu-cache` lacked BGE weights.
The complete pinned BGE-M3 cache is `zenith-v3-r1-embed-cache`, revision
`5617a9f61b028005a4858fdac845db406aefb181`. No new weights were downloaded.
Cached CPU TEI image `cpu-1.8` reports **1.8.3**, not 1.8.0. With existing profile limits
(2048 input, four client batches, auto-truncate), embedding became ready in **58.553 s**;
maximum sampled startup residency was **3.918 GiB** (5 GiB cap, four CPUs). CPU reranking
became ready in **13.859 s**, approximately 1.61 GiB (2 GiB cap, four CPUs).
Sampled maxima are not complete resource peaks.

| Public fixture | Bytes | New upload acknowledgment | Upload to ready |
| --- | ---: | ---: | ---: |
| Small text | 2,801 | 0.817929 s | **24.156350 s** |
| Medium text | 144,683 | 0.441272 s | Did not finish |
| Ten-page PDF | 13,371 | 0.446011 s | Not dispatched |

All three uploads returned 201; duplicates returned 200 in 0.394305, 0.310689 and
0.389816 s. Exactly three jobs were queued. Timings are in-process authenticated ASGI,
excluding network/browser transfer. Small-file upload-to-ready is derived from its
recorded ready event minus its upload start, not from the raw whole-batch field, which
remains null. Small-file parse took 0.000641 s, chunk streaming 0.000202 s, embedding
**20.388223 s**, persistence 0.156880 s and filing 0.016470 s. Embedding dominates that run.
Medium-file embedding remained in progress for **543.040562 s**, then failed after the
resource stop. That duration is not successful throughput.

Twenty searches while ingestion ran had a median wall time **6281.175 ms**; **15 were
degraded**. Range 1172.860–6810.796 ms. No idle samples were collected, so there is no
valid idle/concurrent ratio, percentile SLA or causal regression claim. Event-loop lag
was not written by the original timeout branch and is unavailable for this run.

The run was stopped when host free RAM fell to **381,228 KiB** (about 372 MiB).
Its Docker exit was **137**, elapsed **699.255 s**. Pytest printed “1 passed in 677.58 s”
because that measurement test asserted upload/dedup only; it does not mean ingestion
finished. The benchmark is classified **resource-aborted**, not green. Resource sampling
started late and does not establish complete peaks. Both owned CPU services and the
runner were stopped; unrelated applications stayed healthy. Two preceding Windows
attempts failed with pool timeouts before upload (67.30 and 160.00 s); root cause is
unproven, and these failed logs remain available.

## GPU and next measured bottleneck

The additional GPU TEI local-cache diagnostic failed readiness after a 120-second budget
(157.073 s observed including sampling/cleanup). A bounded strace attempt showed CUDA
device initialization waiting around allocator/memory-protection operations before model
inference; it does not establish the root cause. CUDA independently works: cached WSL
Torch CUDA allocation/synchronization completed in **0.209051 s**, and a driver/context
probe returned success (cuInit 0.0823 s; context retain 0.2661 s). The local Llama proof
also ran through native Ollama's CUDA path. GPU TEI startup remains unresolved; no
CPU/GPU reranking speedup is claimed, especially across different TEI versions.

The immediate pipeline bottleneck is embedding under host memory/CPU contention, with
GPU TEI startup blocking the intended GPU comparison. Small-file parsing/chunking is
already sub-millisecond here, so parser offload has no measured priority. The CPU service
reported 33–34 threads under a four-CPU cap. A controlled single-service run with MKL/OMP
threads limited to four is the next small experiment after sufficient RAM is available;
oversubscription is a hypothesis, not an established cause or a changed product default.
Keep weights, truncation, batches, candidates and versions fixed.

The exposed measurement defect was fixed on this separate benchmark branch: atomic
partial JSON checkpoints after uploads/status/stages/searches, lag persistence on timeout,
bounded preflight subprocesses, resource sampling, and an external runner timeout with
explicit owned-container cleanup. The in-process worker deadline alone waits for graceful
job cancellation. The hard-deadline proof deliberately used a one-second timeout:
exit **124**, owned-container removal exit **0**, elapsed **3.484 s** including cleanup,
and no worker container remained. This is a timeout-path test, not a failed lint result.
Two failed/cancelled-stage checkpoint tests passed in **2.85 s**; lint/format and strict
Linux-target types passed. Cleanup has its own bounded budget; a blocked Docker daemon
can still prevent removal, which is recorded explicitly.

An actual upload-only smoke of final checkpoint code at
`2d7e6941d8e56546c3f832b4abbef1123401d386` passed in **141.39 s**, Docker exit **0**
(165.921 s including runner/setup). It preserved the same three public fixture hashes,
201/pending, 200/deduplicated and three queue jobs. Both stopped model services timed out
health checks, so workers/queries were correctly withheld. This validates the upload and
checkpoint path; it adds no new readiness measurement.

Do not rerun the simultaneous heavy stack at exhausted RAM. Restore resource headroom,
qualify a single fixed service, then repeat with complete resource sampling and the new
external deadline. Full upload-to-ready for medium/PDF, idle queries and simultaneous
model memory remain unmet prerequisites, not inferred metrics.

## Spanish evaluation and identity

[Spanish evaluation](spanish-evaluation.md) and the pinned data manifest still apply:
69,495,568 bytes of public Spanish data are downloaded; synthetic ALIA examples are not
human relevance gold, MIRACL's full corpus is not present, and hard-negative/held-out
candidate panels still require independent relevance review. Jev superiority remains
untested; the supplied key was never used or saved, and no paid call was made.

[Updated MCP decision](mcp-decision.md) records the tested local reference host/Llama and
the proposed future Keycloak boundary. Network OAuth/HTTP deployment remains a later,
separately scoped implementation. A local server cannot prevent a different consumer
from exporting evidence; keep approved hosts, model destination and traces explicit.

Sources: [official SDK](https://py.sdk.modelcontextprotocol.io/servers/),
[SDK release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.2.0),
[Ollama settings](https://docs.ollama.com/faq), [completion fields](https://docs.ollama.com/api/chat),
[Intel MKL threads](https://www.intel.com/content/www/us/en/docs/onemkl/developer-guide-linux/2026-0/working-with-openmp-threads.html),
[NVIDIA WSL guide](https://docs.nvidia.com/cuda/wsl-user-guide/).

Reply draft to Martin, **not sent**:

> He separado el contrato local de judge y la prueba de prefijos de Vite desde tu main;
> ninguno depende del otro, de v10 ni de Jev. Las pruebas específicas pasan y he dejado
> visibles los fallos restantes de las suites completas. El cliente MCP por stdio usa
> permisos y RLS actuales, fuentes acotadas y un modelo local probado. La medición real
> señala embedding y presión de memoria; el arranque de TEI GPU sigue sin resolverse.
> No he publicado ni cerrado ninguna PR y no he iniciado llamadas de pago.
