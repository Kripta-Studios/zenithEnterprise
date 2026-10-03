# Continuation plan based on the measured Zenith results

Completion update, 2026-10-03: [all 128 paired Spanish generated-query and automatic NLI comparisons](spanish-e2e-results-2026-10-03.md)
are finished. The next measured research bottleneck is local lexical admission despite
correct retrieved evidence, followed by generated-claim support. This exposed test set
must not become a new blind confirmation set. The historical recovery checklist below
is complete for this cohort; local product delivery and upstream CI remain separate work.

Date: 2026-10-02. Evidence inspected at commit `d1cb4d7` on
`perf/spanish-e2e-citations`, based on `894d209`. This is a plan, not a completed
end-to-end evaluation or authorization to merge existing branches.

Priority update, 2026-10-03: [Martin's acceptance and model analysis](martin-acceptance-and-model-analysis-2026-10-03.md)
supersedes this plan's delivery order. Complete the independent PR/CI handoff and local
product work without making them depend on Jev research. The recovery checklist below
remains applicable to the frozen evaluation.

**Configuration correction: preserve the current configured local default. BGE is the
stronger measured local research comparator; upstream Compose still defaults to mMiniLM.
Repair the evaluation runner before resuming the frozen Spanish answer-and-citation
comparison. More Jev calls or more datasets are not its immediate constraint.**

## 1. What the results establish

### Completed Spanish reranking study

The MIRACL experiment completed all 648 questions, grouped into 601 article-family
clusters, using published human relevance judgments and the same candidate pools.

| Reranker | nDCG@8 | MRR@8 | Hit@1 | Recall@8 |
| --- | ---: | ---: | ---: | ---: |
| mMiniLM CPU | 0.789051 | 0.849647 | 0.766975 | 0.851878 |
| BGE GPU | 0.817611 | 0.883620 | 0.813272 | 0.851878 |
| Jev | 0.829763 | 0.895139 | 0.827160 | 0.851878 |

Jev minus BGE nDCG@8 is **+0.01215167**, with paired cluster-bootstrap 95% interval
**[+0.00246723, +0.02218987]**. Neither the point estimate nor the lower bound reaches
the preselected +0.02 ranking threshold. MRR and Hit@1 intervals cross zero. Jev's
larger gain over mMiniLM (+0.04071168) does not establish a large gain over the stronger
available local model. Unchanged recall describes permutation of these selected pools,
not whole-corpus retrieval quality.

The BGE whole-query rerank median was 0.443 seconds; Jev's reported median was 0.255
seconds **per pair**, with four concurrent calls. These units cannot support a claim
that Jev is faster for a whole query. This study did not generate answers.

Evidence: [Spanish evaluation](spanish-evaluation.md) and
[machine-readable reranking results](spanish-rerank-results.json).

### Upload and local GPU evidence

The earlier matched embedding trials used the same bge-m3 revision, float32, TEI 1.9.4,
four-CPU cap, batch limits 2048/4, one worker and the same GPU BGE reranker.

| Input | GPU embedding: upload to ready | CPU embedding: upload to ready |
| --- | ---: | ---: |
| 2,801-byte text | 6.021 s | 3.984 s |
| 144,683-byte text | 44.043 s | 203.932 s |
| 13,371-byte text-layer PDF | 51.544 s | 218.860 s |

These are single sequential observations, include queue wait, and exclude WAN latency
and OCR. They suggest useful GPU capacity for larger ingestion jobs; they are not a
general speedup distribution. During CPU ingestion, 6/20 queries degraded after the
interactive embedding budget was exhausted; GPU ingestion had 0/20. Idle query medians
went the other way (GPU 1.528 s; CPU 0.430 s), so do not claim GPU improves every path.

The medium GPU trial spent 17.683 s embedding and 19.867 s persisting, versus 198.137 s
embedding and 1.838 s persisting in the CPU trial. That reversal warrants measurement of
database persistence and shared-host contention before attributing the total to hardware.

Evidence: [follow-up report](followup.md) and
[upload measurements](upload-ready-results.json).

### Spanish answers with mandatory citations: incomplete

The frozen SQAC experiment contains 650 contexts, 16 development questions and 128 test
questions. Both arms use 32 actual hybrid candidates, eight generation passages and the
same pinned local Llama 3.1 8B Instruct model. Published answer spans supply reference
labels; independent local multilingual NLI is intended to check every cited sentence.

Actual multipart upload, ingestion and retrieval completed for 14 files, 939 chunks and
144 questions in two recorded runs. Upload-to-ready was 257.365 s and 234.100 s. The
development-only Jev comparison selected the direct criterion: nDCG@8 0.826643 versus
0.803577 for the citation-specific alternative. That choice is already frozen.

**No complete 128-pair generated-answer result or full independent entailment summary
exists.** `run-llama-final/generated-results.json` contains one completed pair; both
arms abstained. A subsequent Spanish completion with two citations was cached, but its
pair was interrupted by an audit-reader assertion. Neither observation establishes
answer-quality superiority. Later `run-resumed` and `run-safe-final` both stopped at
embedding-service readiness, before uploading or making new paid calls.

The local checks passed: 40 metric/retrieval/prompt/citation tests, two actual PostgreSQL
audit-isolation tests, six budget/cache tests, lint/format and strict Linux-target
Pyright. These checks validate components; they do not replace the unfinished experiment
or a complete current-branch `make check`/upstream CI run.

### Completed SQAC ranking stage within the interrupted run

For this analysis, the complete existing BGE/Jev score files were checked against the
captured panel hash and evaluated with the existing `rank_measures` and `paired_interval`
functions. No model calls or criterion changes were made. All 128 test questions have
32 finite scores per arm; the paired bootstrap has 114 article clusters.

| Ranking-stage measure | BGE | Jev | Jev minus BGE; 95% interval |
| --- | ---: | ---: | --- |
| nDCG@8 | 0.844154 | 0.880481 | +0.036327; [+0.009155, +0.067060] |
| Gold-span recall@8 | 0.890625 | 0.898438 | +0.007813; [0, +0.024194] |
| Questions with a gold-span hit in top eight | 116/128 | 117/128 | +1 question; rate interval [0, +0.024194] |

This is a promising ordering improvement on SQAC, larger than the MIRACL result, but
it is still **not generated-answer or citation-entailment superiority**. The intervals
do not establish a confidently large retrieval gain, and the correct-source hit count
improves by only one question. Do not pool the two datasets or apply the answer-rate
promotion threshold to this secondary ranking score.

All 128 questions have a gold-span chunk somewhere in the corpus, but only **118/128**
have one among the 32 actual candidates. Ten questions lose their annotated source
evidence before either reranker runs. Of the 118 eligible questions, BGE keeps 116 in
the top eight and Jev keeps 117. Under the frozen source-span metric, a reranker cannot
recover the ten missing sources from this same pool. Candidate coverage is therefore
an observed quality bottleneck to investigate on development data after the frozen run.
Better ordering may still help generation; that remains a hypothesis to test.

Local analysis: `.local-evidence/e2e/ranking-stage-analysis.json`.
Captured panel SHA-256:
`94adba601b358793ab804b33dba7c5f2db123c5048fe756e056cf09d105a14a3`.
BGE score SHA-256:
`cc3f2f7b116060944ab23bb20ef97104d20d655d2badd498d596a1b60d803bf5`.
Jev score SHA-256:
`fee6c2bfd167f89bfc936290e0830667769f58835d8255911dea5fd9563293b4`.

Cost across the authorized studies is **14,901 successful Jev calls / $0.378251202** in
usage accounting, including the older 5,173 calls / $0.113911056. The SQAC attempts added
9,728 calls / $0.264340146. Both cumulative caps still apply: 100,000 calls AND $5.
Remaining capacity is 85,099 calls and $4.621748798, not a target to spend. Cached copies
of completions are not additional model calls; cumulative ledger ancestry must stay intact.

Evidence: [frozen protocol](spanish-e2e-protocol.json) and
[execution/design report](spanish-e2e.md). The ignored local evidence directory retains
the raw ledgers, failed runs, snapshots, cached completions and test logs.

## 2. Why the experiment stopped

| Finding | Interpretation | Required response |
| --- | --- | --- |
| Runner waits only 180 s for each TEI service; earlier GPU startup measurements were 555.580, 556.190 and 693.535 s | Readiness budget is shorter than already observed valid startup; latest timeout does not establish provider/model failure | Make readiness budget configurable and measure startup before ingestion |
| Free host RAM fell to 825.8 MiB; monitor stopped our embedder | Actual resource interruption, not answer-quality evidence | Reserve a hardware window and monitor startup as well as scoring/generation |
| OS-suspended training coincided with stalled CUDA initialization; a later unpaused attempt also timed out | Pausing was not shown to provide a usable GPU window; cause is not isolated | Avoid OS suspension as the execution strategy; use a normal job boundary or an available GPU |
| One-file, 939-chunk embedding INSERT exceeded PostgreSQL statement timeout | Product ingestion bottleneck, separate from Jev quality | Reproduce and bound persistence work in a separate change |
| Audit reader omitted the authenticated author's user ID | Harness bug; RLS correctly hid the private log, and the product writer already bound its author | Keep corrected author-scoped read and prove it in a small actual query smoke run |
| Host reader temporarily denied snapshot replacement | Windows measurement-file interaction | Keep atomic bounded retries and read live files with delete sharing |
| New disposable database UUIDs changed tied candidate pools; whole-cache replay refused 259 new passages | Rebuilding the database creates new work and experimental variation | Retain the experiment database between stages and score every genuinely new pair |
| 10/128 annotated answer sources are absent from the 32-candidate pool despite existing in the corpus | A retrieval coverage loss that neither reranker can repair within the fixed pool | Keep this run frozen; investigate hybrid retrieval and chunk coverage on development data for a later holdout |
| Cached Qwen tag was thinking-only and failed neutral readiness before test generation | Model alias was unsuitable for the fixed output policy | Keep the effective pinned Llama model in both arms; retain the initial protocol |

The competing training was restored, verified by
`.local-evidence/e2e/authorized-training-resumed.json`. No evaluation process was active
at this inspection. The idle experiment embedder was stopped; other applications were
left running. Do not describe the last readiness attempts as successful resumptions.

## 3. Ordered implementation plan

### P0 — Repair orchestration before another full run

Implement this in the evaluation branch, without changing product ranking or generation.
Main edit points: `scripts/local-first/run_spanish_e2e.py` for readiness, phase reporting
and cleanup; `scripts/local-first/docker_checks.py` for exit propagation; the opt-in
`backend/eval/tests/test_spanish_e2e_pipeline.py` fixture for database/stage retention.

1. Add a configurable TEI readiness budget, initially **900 seconds**, based on the
   recorded startup observations. Record cold/warm start, `/info`, model revision,
   precision, batch limits, device and elapsed time. On failure, retain diagnostics and
   exit; do not extend deadlines indefinitely. Changing this execution budget does not
   change the frozen answer-quality protocol.
2. Start RAM/GPU sampling before starting each model. Persist the phase transition
   immediately, rather than leaving the status at `waiting_for_resources` while CUDA
   initializes. Require a successful neutral embedding or reranking request as well as
   health and identity checks before the full stage.
3. Fix cleanup for failures before the pytest runner is created: stop only services
   started by this invocation, wait for its owned children and retain their exit codes.
   Currently the readiness failure can leave the embedder running. Never terminate or
   suspend another project's job as an automatic recovery action.
4. Propagate nonzero pytest results through `docker_checks.py`'s process exit, while
   preserving its structured check report. Keep the controller's explicit report checks.
5. Decouple the opt-in stages from disposable-test teardown. Use one isolated evaluation
   database/volume and run ID across upload, capture, scoring and actual `/query` stages.
   Validate the corpus and candidate hashes on resume. Keep original IDs and the queue
   state; do not restore cached vectors into a different corpus silently. This is an
   evaluation fixture using the existing database, not a new vector store.
6. Test one actual upload and one generated Spanish response with citation binding and
   author-scoped audit reads. Use a development or separate public smoke question. Prove
   interruption/resume, the readiness-failure exit and owned-process cleanup before 128
   questions. Keep live-file reads compatible with atomic replacement.

**Exit gate:** a smoke run completes from upload to audited answer, a simulated stage
failure resumes against the same database without re-ingestion, and cleanup leaves no
owned model/runner orphan. No new paid calls are necessary for the local smoke test.

### P1 — Finish the frozen paired Spanish experiment

1. Arrange a GPU window after the competing job reaches a normal completion/checkpoint
   boundary. Verify RAM headroom and model residency with real requests. If shared
   hardware remains necessary, record that condition and withhold isolated latency claims.
2. Reuse the existing SQAC fixture, 128 test IDs, 16 development IDs, seed, source hashes,
   effective generator digest, original product prompt and frozen direct Jev criterion.
   Keep 32 candidates and eight generation passages in both arms. Do not tune on these
   test outcomes or substitute mMiniLM as the principal comparator.
3. Upload/capture once through the existing authenticated API and worker. Validate all
   14 ready documents, 939 chunks and 144 question IDs. Match original successful pair
   scores by exact question, filename, character offsets and full passage text. Independently
   score every uncached pair with its actual provider; preserve cumulative budget ancestry.
4. Run the 128 paired real `/query` calls in the predefined balanced arm order. Assert
   unchanged retrieval identities/order, bound citation identities and author-visible
   audit entries. Reuse a completion only for the same complete request and model digest.
   Keep abstentions, invalid markers and output-limit failures in the denominator.
   Record response language separately: the observed no-evidence canned abstention was
   English. Do not translate or replace it post hoc to improve the frozen result; a
   Spanish-abstention product correction would be a separate subsequent change.
5. After the complete paired run, unload the owned generator and run the pinned local
   mDeBERTa NLI judge in CPU float32. Check the independent Spanish sanity examples first.
   Score every sentence against its cited sources with explicit source windows.
6. Produce `spanish-e2e-results.json` and update the report with all 128 pairs, primary
   rate, paired article-cluster confidence interval, retrieval quality, answer F1,
   citation coverage/precision, abstentions, errors, cost and source/log hashes.

**Exit gate:** 128/128 unique pairs, successful actual integration test, all audit checks,
complete independent grading and reproducible aggregate. One good example is not this gate.

The frozen primary metric requires reference-answer containment, a valid citation to its
annotated source span, a marker on every sentence and NLI entailment >=0.8 for every
sentence. The meaningful gain is at least **+2 percentage points**, with 95% CI lower
bound >0. The clearly larger gain requires **+5 points**, with lower bound >=+2 points.
Use the existing 2,000 paired article-cluster bootstrap resamples and seed 20261002.
These answer-rate thresholds are distinct from the earlier nDCG@8 threshold.

### P2 — Improve ingestion in a separate, reviewable product change

Reproduce the one-file persistence timeout using the same public corpus, then profile
queue wait, parsing, chunking, embedding, database insert/commit and time to `ready`.
Bound embedding-row INSERT sizes using the existing persistence path, preserving the
document's atomic visibility, retry idempotence, cancellation and RLS. Do not mark a
partially indexed document ready. Keep current streaming uploads, deduplication, worker,
TEI batching, PostgreSQL schema and GPU Compose override.

Test the unsplit 939-chunk document as well as the 14-file case, duplicate uploads,
failure/retry and cross-tenant access. Do not hide the failure by increasing PostgreSQL's
timeout or splitting customer documents outside the product.

Next measure embedding contention during ingestion with the existing CPU/GPU fixtures
and concurrent authenticated queries. Compare smaller ingestion batches or a bounded
query-priority policy on development workloads. Establish a no-regression gate for
interactive p95/fallback rate and upload-to-ready before changing worker concurrency.
The existing GPU profile's larger batch/depth/worker settings remain unqualified here.

**Exit gate:** the previously failing unsplit file reaches ready without a timeout,
retries do not duplicate chunks, isolation holds and repeated measurements show where
time was removed. Report median/p95 across repeated, alternating device trials; retain
failures and distinguish warm startup, cold startup and steady-state throughput.

### P3 — Confirm MCP and upstream integration separately

Preserve the independent judge-contract and Vite-prefix branches. Verify their latest
upstream CI results against their exact heads before proposing adoption; existing local
checks are not proof that Martin's pipeline is green. Leave the original 15 PRs open
and unchanged unless separately authorized.

Keep the accepted local-client/local-model direction and existing stdio reference.
The REST experiment above does not evaluate an MCP client's discovery/tool-selection
path. Qualify that path separately: upload through the existing multipart helper, poll
authorized status, retrieve permitted sources, generate a Spanish answer locally and
reauthorize its citations. Include revocation, cancellation, cross-tenant rejection and
verification that source text is not sent to a cloud model or telemetry endpoint.

Reuse the existing Keycloak-auth branch for later intranet deployment. Bind issuer,
audience, principal mapping, DNS/TLS and secret provisioning to actual deployment inputs.
Do not build another identity system or a general-purpose agent host. Evidence and scope:
[MCP decision record](mcp-decision.md), [follow-up](followup.md) and
[publication record](publication.json).

## 4. Decision after the complete result

| Complete result | Action |
| --- | --- |
| Gain fails the frozen meaningful threshold | Keep BGE; publish the negative/null result; stop further paid tuning on this test set |
| Meaningful threshold passes but clearly-larger threshold fails | Report a limited measured gain; product default stays local pending the product/privacy decision |
| Clearly-larger threshold passes | Present the complete Spanish answer/citation evidence to Martin; it still does not authorize private-document egress or Jev deployment |
| Run or independent grading remains incomplete | Report only validated component/ingestion evidence; no superiority claim |

If further Jev optimization is warranted, diagnose errors only after this frozen run:
missing gold evidence in the candidate pool, incorrect reranking, answer generation,
citation binding and entailment failure are different problems. Tune criteria or retrieval
only on development data and freeze a **new untouched holdout** before the next comparison.
Already inspected test outcomes cannot become evidence for a retuned prompt's superiority.

Do not download more public data until the existing experiment is runnable and a specific
domain gap is identified. ALIA legal/admin synthetic examples are useful fixtures, not
independent proof of generated legal correctness. Published QA spans eliminate the need
to create new extractive labels; automatic NLI still does not supply independent human
judgments of every generated claim. SQAC results cannot establish private-client or legal
performance without a relevant additional evaluation.

## 5. Immediate next handoff

The next coding task is **P0 orchestration repair plus its local smoke proof**. Then run
P1 once with the existing data and ledgers. Do not launch the current unmodified runner
again with its 180-second readiness deadline. Do not start a paid tuning sweep, retune the
frozen criteria, add a vector database, implement distributed Jev quotas or merge branches
as part of this plan.

After measurements and appropriate checks complete, publish only the intended new branch
with a normal push, exact results and preservation checks. Move the experiment note to
`to-test` only after its required work actually passes. Keep raw datasets, model weights,
credentials and source-bearing completions in ignored local storage.
