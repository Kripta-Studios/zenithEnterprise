# Follow-up: implemented changes and measured results

This record supersedes the outstanding items in report.md and continuation.md. Earlier
failed attempts remain retained. The user authorized publishing the work and then paid Jev
evaluation within both 100,000 calls and $5. Existing upstream PRs/main and fork history
remain preserved. Work is isolated under zenithEnterprise-v3-clean/.scratch.

## Delivered code

- The two accepted extractions remain independent from Martinhdeez main
  33b48812c95150348c52d2519159780252c92db2: judge contract
  36f4f7d7155dee047d9eb8f9528de312ba3b59d7 and proxy guard
  9e9bd377dbdad1b3912c4b8aa147c2f8009e7cd2. Neither depends on Jev, v10 or each other.
- fix/deterministic-test-timing controls upload completion explicitly, bounds Vitest's
  worker pool and assigns a definite filesystem timestamp mutation. Product upload
  concurrency and the read-only checkout guard are unchanged. Head 9b5a84f has only a
  documentation addition after tested frontend head b7615dd.
- feat/mcp-intranet-auth extends local MCP 5f590bb3f1ca24e4e20dafb2ee995636ab25f7eb.
  It adds a separately invoked loopback Keycloak resource server, protected-resource
  discovery, explicit subject enrollment, bounded introspection and current Zenith
  permissions/token-version checks. It reuses the application-role RLS read service and
  streaming upload CLI. No new schema/dependency versions or route in the product API.
- perf/local-first-baseline adds real TCP upload/ready measurements, resource monitoring,
  frozen Spanish reranking and durable local spend accounting. An optional image-only
  Blackwell overlay extends the existing GPU Compose file. Model caches, batching,
  deduplication, ingestion and queue implementations are reused.
- fix/embedding-final-backoff independently removes the sleep after the final failed
  embedding attempt. Queries keep one attempt and the five-second timeout; ingestion
  keeps three attempts with one- and two-second delays between them. This removes a
  needless extra second on interactive failure and four seconds on terminal ingestion
  failure. CPU contention measurements below precede this fix.

## Checks

The original final local MCP commit completed its full backend suite: 911 passed and
12 skipped in 2,143.39 seconds, exit 0. This closes the earlier incomplete-suite item.
The new authenticated MCP feature checks passed 45 with one optional-model skip in
392.47 seconds; the final bounded-verifier tests passed 15 in 200.71 seconds. The corrected
real Keycloak 26.8 PKCE/current-Zenith-authority/logout proof passed in 20.10 seconds,
exit 0, on final source f344b008fa9543ba8b132de21bcd8515603b8930.

The authenticated MCP branch completed its final full Linux backend suite: 927 passed,
13 skipped in 1,982.03 seconds, exit 0 (runner wall time 2,010.781 seconds). The independent
timing branch completed its full suite: 882 passed, 11 skipped in 1,904.77 seconds, exit 0
(runner wall time 1,932.945 seconds). These are separate branch runs, not a combined merge.

The unchanged judge and proxy extractions retain their independent focused results:
29 passed / 155.91 seconds and 7 passed / 34.74 seconds, respectively. Their older full
suites still record the upstream timestamp-test failure; the separate timing branch
repairs that test. No extraction history was changed to hide or combine those results.

The independent final-backoff fix, 595bbe2e31756b15430a54d225280a596145ac19, passed all
122 embedding/retrieval tests in 238.35 seconds, exit 0 (runner wall time 262.660 seconds).
Its strict Linux-target pyright, backend Ruff lint and format checks also passed.
No full-backend-suite result is claimed for this small separate branch.

Frontend on pinned official Node 22.23.3/npm 10.9.9: all 43 files / 437 tests passed in
470.15 seconds. Type checking passed; the final production build transformed 2,247 modules
and completed in 79 seconds. Its existing large-chunk warning remains. Backend strict
Linux-target pyright passed using the complete Windows dependency environment; actual
backend tests ran on Linux with disposable ParadeDB and the application database role.
Lint/format checks passed. Shipped dependency license check passed, exit 0; the unchanged
optional MCP dependency closure was already checked in the preceding continuation.
The deterministic checkout tests separately passed 6 in 11.77 seconds. Four accounting
and metric regressions passed in 0.091 seconds. Blackwell Compose configuration retained
both inherited NVIDIA reservations, cache mounts and batch flags. Runtime proof is the
measured isolated services; this is not a production Compose deployment.
The measured GPU reranker requires the existing TEI_RERANK_MODEL setting to select
BAAI/bge-reranker-v2-m3; the overlay alone retains the development mMiniLM default.

The retained failed attempts include an invalid Vitest min/max invocation, a types run
against the wrong dependency environment, a manual obsolete initialize request against
modern MCP, incomplete Keycloak fixture cookies/profile/audience/subject configuration,
and a resource-aborted full-suite attempt. Final checks replace those attempts, rather
than treating them as passes. A resource guard stopped the owned models at 944.86 MiB
free RAM. Subsequent measurements and checks were separated; unrelated applications
were preserved.

## Upload and query measurements

Both completed trials used the same SQAC dev fixtures, SHA
 ec748f222626e5081a34193ca469bcf8112092837678a6948a2d6ae7d6629d1a,
actual loopback TCP multipart, real authenticated REST/application-role RLS, existing
streaming/dedup/Procrastinate ingestion, one worker, batches of 2,048 tokens / four inputs,
bge-m3 revision 5617a9f61b028005a4858fdac845db406aefb181 and float32 TEI 1.9.4 embeddings.
Only the embedding device changed; the GPU BGE float16 reranker remained fixed. This
is a hybrid CPU-embedding/GPU-reranking comparison, not a complete CPU-only stack.

| Fixture | Bytes | GPU embedding: upload to ready | CPU embedding: upload to ready |
| --- | ---: | ---: | ---: |
| small.txt | 2,801 | 6.021 s | 3.984 s |
| medium.txt | 144,683 | 44.043 s | 203.932 s |
| public-qa.pdf | 13,371 | 51.544 s | 218.860 s |

All six new-upload acknowledgments were 201/pending; duplicates were 200 with identical
IDs, and exactly three jobs were queued per trial. All final documents were ready.
Upload-to-ready includes queue wait behind preceding files. The PDF is a text-layer public
fixture, not scanned-document/OCR qualification.

| Query phase: 20 samples each | GPU embedding median / p95 | CPU embedding median / p95 | Degraded GPU / CPU |
| --- | ---: | ---: | ---: |
| During ingestion | 1.929 / 5.036 s | 5.171 / 6.432 s | 0 / 6 |
| Idle | 1.528 / 2.005 s | 0.430 / 0.804 s | 0 / 0 |

All queries returned HTTP 200. The fixed visible corpus was the first file, containing
three passages, with limit eight and query concurrency one. Samples began while the
worker was active; the last request can finish after queue drain. Reported p95 uses the
zero-based sorted index floor(0.95*n), which is the maximum for n=20. These are sequential
single trials on a shared laptop, with changing load/caches and no randomized repetitions;
query distributions and persistence timings do not establish a general hardware speedup.

The medium file spent 17.683 s embedding / 19.867 s persisting on the GPU trial versus
198.137 s embedding / 1.838 s persisting on the CPU trial. The persistence reversal shows
why whole-pipeline speed cannot be attributed solely to the device. The next measured
CPU bottleneck is shared embedding service contention: six queries exhausted the existing
five-second interactive budget during ingestion. Smaller ingestion batches or a query
priority policy should be measured against these same fixtures before changing defaults.
The GPU workload completed without that fallback. Existing larger GPU profile defaults
(16,384/32, four ingestion workers, depth 100) remain unqualified by this small baseline.

GPU BGE startup needed 693.535 s in the first successful bounded observation; its later
restart needed 555.580 s. GPU embedding became ready in 556.190 s. The matched CPU 1.9
embedder became ready in 37.675 s under the later quieter host conditions. Earlier short
readiness deadlines were insufficient. The separate cached mMiniLM GPU attempt failed
because its CPU cache contained ONNX files without GPU-readable model weights; that
failure does not diagnose the earlier CUDA stalls. Complete BGE safetensors served on the
RTX 5070 Ti. The CPU four-thread 1.8 trial also reached readiness, but its later RAM guard
abort prevents a throughput claim from that trial.

Pinned GPU digest: bd8e5b1954146f7fe8590b64b959bc194433c6c38c036592a84d736841ca9400.
Pinned CPU digest: 2538ea1c9640d3763b15af668039d24172d063b42337b0c27796fc2be180c78d.
Both reported TEI 1.9.4. Raw readiness/resources, source/tree snapshots and log hashes are
in upload-ready-results.json and followup-verification.json.

## Spanish Jev decision

Published MIRACL human relevance judgments replace the proposed new manual annotation
work. All 648 Spanish dev queries, positive/negative passage IDs and labels were checked
against pinned original qrels. SQAC and ALIA legal/admin datasets are also downloaded.
Data total 72,150,538 bytes; BGE model weights/tokenizers were downloaded separately.
Raw datasets, weights, runtime credentials and temporary logs remain outside Git.

The frozen panel was evaluated once with Jev-1.13.0 and reused for both local models.
5,173 successful calls, zero errors/fallbacks, 2,712,168 input tokens, $0.113911056 accounted
usage. No further calls were needed for BGE. The API key was used only in memory and is
absent from the repository. Budget accounting is local evaluation tooling, not a product
or distributed quota service.

Jev nDCG@8 was 0.829763; mMiniLM 0.789051; BGE 0.817611. The paired family-bootstrap
Jev-minus-BGE gain was +0.01215167, 95% interval [+0.00246723, +0.02218987], below the
frozen meaningful-gain threshold of 0.02. The stronger mMiniLM gain was +0.04071168,
interval [+0.02866289, +0.05348700]. Keep the local product path. This judged-pool Wikipedia
experiment does not prove whole-corpus retrieval, legal correctness or better generated
answers. Exact protocol, metrics, limits and download hashes are in spanish-evaluation.md,
spanish-rerank-results.json and spanish-data-manifest.json.

## Deployment and publication boundaries

Keycloak proof is disposable loopback development infrastructure, now stopped. The real
intranet endpoint still needs organizational DNS/TLS, issuer ownership, explicit Zenith
user enrollment and secret provisioning. These are deployment inputs; a fake public realm
is not a production identity installation. Other desktop MCP applications were not
qualified; the fixed official SDK local client/model and selected-file CLI are the tested
consumers. Private content must remain with that local consumer/model.

Existing upstream PRs and fork branches are preserved. The accepted extraction branches
remain unchanged. Follow-up commits are published to the authorized fork branches only,
without rewriting history or merging main. Remote Actions require a PR/main event under
the existing workflow; branch pushes alone do not establish remote CI success.
The post-push [publication audit](publication.json) records the exact published code/results
heads, preservation of the other 20 existing fork heads, upstream main and all 15 open
upstream PR heads/states. Its subsequent documentation-only commit is pushed normally.
