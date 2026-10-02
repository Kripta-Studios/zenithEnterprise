# Zenith: model evidence, Martin's acceptance requirements, and the next delivery plan

Date: 2026-10-03 (Europe/Madrid). GitHub state rechecked on 2026-10-02 at approximately
23:00 UTC. Analysis starts from local commit `24cafcc` on
`perf/spanish-e2e-citations`; that branch descends from local-first baseline
`894d209f51da011365e8ae850c8bff222217890f`.

**Deliver the two independent local changes for upstream review first. Keep local processing
as the product direction. Improve upload-to-ready reliability and qualify the local MCP
consumer. Finish the frozen Spanish Jev experiment separately; its outcome cannot authorize
private-document egress or qualify the deployment topology.**

This document supersedes the priority order in
[the earlier continuation plan](continuation-plan-2026-10-02.md), while retaining that
plan's detailed evaluation recovery checklist. It analyzes completed and incomplete work;
it does not report a new benchmark, change product defaults, submit PRs, or authorize merging.

## 1. What Martin asked for, and what is actually delivered

Martin's review contains two distinct decisions: accept useful local engineering slices,
and withhold adoption of Jev on the evidence and product constraints available to him.
His later MCP/upload request expands the local product work; it does not reverse the
egress objection.

| Requirement | Verified state | Remaining acceptance evidence |
| --- | --- | --- |
| Provider-neutral judge, independent of the stack | Implemented, tested, and pushed as a direct child of upstream main | A new independent upstream PR and green CI for its exact candidate |
| Vite proxy-prefix guard, independent of the judge | Implemented, tested, and pushed separately from the same main | A second independent upstream PR and its own green CI |
| Upstream pipeline evidence | Main has a successful run; all 15 original PRs have empty check rollups and their recent runs require approval | Maintainer approval of fork Actions, then actual job results for the two new PRs |
| Leave the other 13 PRs open | All original 15 PRs remain open, with their recorded heads unchanged | Continue preserving them; no automatic closure or history rewrite |
| Local GPU performance | Matched embedding CPU/GPU measurements exist; historical reranker GPU pilot exists | Repeatable timings, resource accounting, simultaneous stack qualification and rollout evidence |
| Optimize uploads as well as search | Existing streaming/dedup/queue reused; real upload-to-ready trials expose persistence and contention problems | A focused reliability fix and repeatable query-under-ingestion qualification |
| Integrate MCP | Local stdio reference and optional loopback Keycloak branch implemented and tested | Actual selected interactive client, tool/upload compatibility and deployment qualification |
| Stronger Spanish Jev evidence | MIRACL ranking finished; SQAC ranking finished; generated-answer comparison incomplete | Complete paired Spanish answers, citation/entailment grading, uncertainty and failure accounting |
| Independent labels | Published human MIRACL/SQAC references replace implementer-created references | They do not human-adjudicate every generated claim; disclose the automatic judge's limits |
| Preserve private on-premises isolation | Accepted extractions and local MCP do not require Jev | A future external provider still needs Martin's separate product decision |
| Safe multiworker external processing | No shared Jev quota/breaker qualification has been established | Do not enable Jev in the production API/worker topology or build a distributed quota system under this plan |

**Published fork branches are not upstream PRs.** The live upstream PR list contains
the original #1–#15 only. None uses either standalone branch. This is the main unfinished
delivery step relevant to Martin's acceptance, independent of GPU availability or Jev scores.

### Exact accepted candidates

Upstream main remains `33b48812c95150348c52d2519159780252c92db2`.
Both candidate commits have this commit as their immediate parent.

| Logical contribution | Fork branch and head | Diff from upstream main |
| --- | --- | --- |
| Old upstream [#2](https://github.com/Martinhdeez/zenithEnterprise/pull/2): local judge boundary | `feat/local-judge-contract-standalone`, `36f4f7d7155dee047d9eb8f9528de312ba3b59d7` | 7 files, +368/−6; five implementation files, one contract test file, one plan note |
| Old upstream [#6](https://github.com/Martinhdeez/zenithEnterprise/pull/6): proxy guard | `fix/vite-proxy-prefix-guard-standalone`, `9e9bd377dbdad1b3912c4b8aa147c2f8009e7cd2` | One integration-test file, +76/−1 |

Judge tree: `839b36ca7075969e9e108d2feaebf611d850bfec`.
Proxy tree: `e488ce8393928392c8442b540fd79c77e9f646bd`.

The judge boundary is used by the TEI path. Candidate UUIDs survive repeated text;
assessed/failed/skipped outcomes partition the requested IDs exactly; assessed rank values
must be finite. Rank values are provider-neutral, not required to be probabilities.
Invalid or incomplete batches fall back as a whole, cancellation propagates, and one
deadline bounds sequential rerank batches. It adds no Jev client, dependency, migration,
external-processing flag, or default change.

The proxy change tests the actual configured proxy object, missing prefixes, declared/literal
API targets, intentional omissions, unrelated strings, and existing Nginx coverage.
It is a CI prefix-coverage regression guard, not a runtime URL or SSRF validator.

Historical naming is misleading: the packet increment called “PR06” inside the series is
upstream #9. Martin's requested old upstream #6 is the proxy guard. Use upstream numbers
and the exact branch names in new PR descriptions.

### Tests belong to their exact branches

| Candidate | Focused checks | Full backend | Full frontend |
| --- | --- | --- | --- |
| Judge | 29 passed, 155.91 s | 900 passed, 11 skipped, 1 failed, 303.17 s | 436 passed, 1 failed, 50.46 s |
| Proxy | 7 passed, 34.74 s | 885 passed, 11 skipped, 1 failed, 238.14 s | 436 passed, 1 failed, 264.79 s |

Both full backend runs retain
`test_read_only_checkout.py::test_a_rewritten_file_is_seen_even_at_the_same_length`.
The frontend failures were `uploadQueue.test.ts:138` for judge and
`Analytics.test.tsx:65` for proxy. These are environment/timing-sensitive observations
in unchanged tests; they are not permission to ignore a red candidate pipeline.

Strict Linux-target types, Ruff, licenses, frontend types and build passed. The actual Vite
smoke returned JSON for all twelve configured API prefixes; intentional omissions returned
SPA HTML. Six public Spanish TEI fixtures gave identical candidate IDs, order and scores
through the old and adapted paths. Their 118.529 versus 121.455 ms warm medians are a small
compatibility check, not a model-quality or performance study.

The separate deterministic-timing branch has a full backend result of 882 passed /
11 skipped and a frontend result of 437 passed across 43 files. Those results do not
make the two extraction branches green. Likewise, historical v10's 1,013 backend passes,
9 skips and 450 frontend passes do not qualify either new composition.

Evidence: [extraction report](report.md), [local check record](verification.json),
[follow-up](followup.md), and [draft PR descriptions](pr-drafts.md).
The draft descriptions predate publication and contain an outdated “not published”
narrative; prepare current descriptions when submitting, rather than copying that claim.

### Actual CI state

Of 21 returned upstream workflow runs, 16 conclude `action_required`; five older
main runs succeeded. The current main SHA has a
[successful main run](https://github.com/Martinhdeez/zenithEnterprise/actions/runs/34726168540).
The original [judge run](https://github.com/Martinhdeez/zenithEnterprise/actions/runs/36438187873),
[proxy run](https://github.com/Martinhdeez/zenithEnterprise/actions/runs/36438230857), and
[report run](https://github.com/Martinhdeez/zenithEnterprise/actions/runs/36439616588)
require action.

This is an approval gate, not evidence of a test failure in those unexecuted PR jobs.
The workflow runs on pushes to main and on PRs; pushing a feature branch alone does not
supply the requested PR CI. A maintainer's promise to approve Actions is not an observed
approval, green CI result, or merge authorization.

## 2. Model inventory: distinguish servers, weights, tasks, and proofs

“TEI” identifies a serving runtime, not a single reranking model. Effective Compose
defaults and the runtime's `/info` response matter more than an application constant.
Upstream Compose defaults `TEI_RERANK_MODEL` to mMiniLM, although the Python reranker
has a BGE model constant. The neutral contract records provider `tei`, not model
metadata. This discrepancy is a reason to record serving identity explicitly, not a
claim that BGE has already become the deployed default.

| Model/configuration | Role and completed evidence | Decision |
| --- | --- | --- |
| `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | Local reranker; historical CPU/GPU pilot, QASPER comparator, Spanish MIRACL CPU comparator | Preserve the current configured product default; report its actual runtime identity |
| `BAAI/bge-reranker-v2-m3` | Stronger local GPU reranker; MIRACL and SQAC ranking | Required research comparator before crediting Jev with a large local-baseline advantage; product replacement still requires measurement/review |
| `jev-1.13.0` Noul | External rubric-based pair scoring; QASPER, MIRACL and SQAC ranking; separate support and segmentation probes | Research only on approved public fixtures; no private default |
| `jev-1.13.0` Score6 | Distribution-based expected utility; pilot and 40-question QASPER | Retain validation failures; no evidence that it is preferable to Noul for this product |
| `BAAI/bge-m3` | Embedding model; retrieval, ingestion and matched CPU/GPU embedding trials | Reuse current embeddings/batching; it is not the BGE cross-encoder reranker |
| Cached `qwen3:4b`, actually Qwen3-4B-Thinking-2507 | Failed neutral Spanish readiness within the non-thinking 256-output-token protocol | Unsuitable for that frozen execution configuration; this is not a general model-quality verdict |
| `llama3.1:8b-instruct-q4_K_M` | Frozen SQAC generator; neutral readiness and isolated actual Spanish outputs | Use the same pinned generator for both arms; the 128-answer study remains unfinished |
| `llama3.2:3b` Q4_K_M | Local MCP reference-host model; small real citation proof | A working transport/client reference, not a demonstrated best Spanish QA model |
| `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` | Independent automatic entailment judge; Spanish positive/negative sanity probes | Complete offline grading; do not call it human adjudication or calibrated certainty |

### Pinned identities

| Item | Revision or digest |
| --- | --- |
| mMiniLM reranker | `1427fd652930e4ba29e8149678df786c240d8825` |
| BGE reranker | `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` |
| BGE-M3 embedding | `5617a9f61b028005a4858fdac845db406aefb181` |
| Llama 3.1 cached model | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` |
| Llama 3.2 cached model | `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72` |
| Multilingual NLI | `8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c` |

The frozen SQAC generator uses temperature 0, seed 20261002, context 8192 and output cap

256. Cached Qwen consumed its cap on reasoning despite the neutral no-thinking probes;
the generator change preceded test generation and did not select a model using test-answer
quality. Llama 3.1's neutral readiness took 47.477 s on shared hardware. One isolated
completion later took 447.249 s under contention. Neither observation is a production
latency distribution.

The MCP reference's “Thirty days. [1]” proof took 3.203 s generation; a guarded repeat
took 18.469 s with concurrent checks. This proves a usable local reference, not superiority
over Llama 3.1. Earlier two-question upstream/integrated Llama 3.1 checks ran with TEI
unavailable and degraded fallback, so they do not compare functioning rerankers.

NLI runs on CPU float32 with explicit overlapping windows for premises exceeding 512
tokens, without silent truncation. Spanish positive/negative sanity entailment scores
were 0.99770844 and 0.01011454. Two sanity examples validate wiring; they do not estimate
Spanish claim-grading error. The fixed 0.8 cutoff is a grading rule, not an 80% correctness
guarantee. Keep sentence/window diagnostics when full grading is completed.

## 3. Evidence ledger: what each experiment can establish

Intervals below are the original reports' paired cluster-bootstrap 95% intervals.
“Complete evidence,” nDCG, citation identity, entailment, and answer correctness are
different outcomes. Do not pool them into one superiority percentage.

### 3.1 Public pilot: Martin's criticism still applies

Ten queries, only one Spanish, used eight short public-source paraphrases and implementer
labels. All four configurations reached recall@2 = 1.00.

| Reranker | nDCG@8 | Top-1 | Rerank median |
| --- | ---: | ---: | ---: |
| mMiniLM CPU | 0.968 | 9/10 | 645 ms |
| Same weights, GPU | 0.968 | 9/10 | 272 ms |
| Jev Score6 | 1.000 | 10/10 | 2,240 ms |
| Jev Noul | 1.000 | 10/10 | 2,154 ms |

One Spanish seismic-intensity question explains the quality difference. Score6 is
3.47 times the CPU stage latency and 8.24 times the GPU stage latency. The local
645-to-272 ms improvement is useful evidence, but runtime version changed with device:
do not attribute the whole 2.37-times ratio to hardware alone or call it an SLA.
An additional CPU observation of 889 ms also demonstrates local variation.

This pilot cannot justify Jev adoption, independently judged Spanish answer quality,
or a new default. [Pilot report][pilot].

### 3.2 QASPER: genuine English evidence-ranking gains, with important denominators

| Cohort | Local mMiniLM evidence result | Jev Noul result | Paired evidence gain |
| --- | --- | --- | --- |
| 40 development papers | 67.5% complete | 75.0% complete | +7.5 pp, CI [−5.0, +20.0]; 5 wins / 2 losses |
| 240 selected test papers, 193 addressable questions | 106/193 = 54.9% | 128/193 = 66.3% | +11.4 pp, CI [+6.7, +16.6]; 25 wins / 3 losses |
| 176 new disjoint test papers, 147 addressable questions | 75/147 = 51.0% | 93/147 = 63.3% | +12.2 pp, CI [+6.1, +18.4]; 20 wins / 2 losses |
| Descriptive join, 416 selected papers / 340 addressable | 181/340 = 53.2% | 221/340 = 65.0% | +11.8 pp, CI [+7.9, +15.6]; 45 wins / 5 losses |

The 40-case Score6 result of 75.0% is conditional on only 32 valid batches out of 40.
Eight batches failed probability-mass validation. A subsequent 64-call diagnostic
replay could not reproduce the failure; it neither erases the failures nor adds independent
quality samples.

The larger 206-question development TEI-only check found dense complete evidence 53.4%
versus TEI 51.0%, with equal-paper delta −0.9 pp, CI [−6.2, +4.7]. Thus the favorable
40-case local comparison does not describe all 206 questions; Jev was not tested on
the remaining 166 in that experiment.

In the 240 test cohort, nDCG was 0.773 versus 0.848, delta +0.076, CI [+0.045, +0.107],
on 184 candidate-hit cases. Nine addressable candidate misses stay in the complete-evidence
denominator but are outside nDCG. The 176 new cohort has 132 candidate hits, 15 misses,
and 29 selected cases without usable annotated spans; nDCG is 0.734 versus 0.887,
delta +0.153, CI [+0.107, +0.196], on the 132 candidate-hit cases.

The 176-paper extension is the fresh, disjoint confirmation. The 416-paper combined
result reuses the already inspected 240 cohort and is descriptive, not 416 newly blind
questions. Do not count reused predictions as new paid calls or a replication.

The 240 cohort's batch p50/p95 was 224/296 ms local versus 1,962/2,087 ms Jev.
The new 176 cohort was 46/315 versus 2,308/2,611 ms; its unusually small local median
is a warm-run observation, not an enterprise SLA.

**Conclusion:** there is credible task-specific human-labeled English ranking evidence
against mMiniLM. It is not a BGE head-to-head, Spanish generated-answer result, upload
benchmark, or permission to send private documents externally.
[40-case report][qasper40], [240-case report][qasper240],
[176-case report and descriptive join][qasper176].

### 3.3 MIRACL Spanish: compare against the stronger local reranker

All 648 questions and 601 article-family clusters were evaluated on matched human-judged
positive/negative pools, with BM25 choosing at most eight candidates. Shared query/passage
caps were 512/1,000 characters.

| Ranking | nDCG@8 | Interpretation |
| --- | ---: | --- |
| BM25 | 0.699709 | Selected-pool baseline |
| mMiniLM CPU | 0.789051 | Current-model local comparison |
| BGE GPU | 0.817611 | Stronger local comparison |
| Jev | 0.829763 | Small further ranking gain |

Jev minus mMiniLM is +0.04071168, CI [+0.02866289, +0.05348700].
Jev minus BGE is **+0.01215167**, CI **[+0.00246723, +0.02218987]**.
The latter does not reach the recorded +0.02 point-estimate/lower-bound ranking criterion;
MRR and Hit@1 intervals include zero. All arms have the same 0.851878 Recall@8 because
they reorder the same selected pools.

The BGE whole-query median/p95 is 0.443/0.727 s; mMiniLM CPU is 1.488/3.201 s.
Jev's 0.255 s median is **per pair**, with four concurrent calls. Comparing it directly
to whole-query BGE latency would be wrong. Eight calls with shared limits, network tails
and provider queueing require a measured whole-query distribution.

MIRACL is public Spanish Wikipedia ranking, not full-corpus retrieval or generated QA.
Full-passage labels can disagree with a truncated rendering; training overlap is unknown.
Article-family clustering limits dependence but does not eliminate every topical overlap.
[Spanish study](spanish-evaluation.md), [aggregate results](spanish-rerank-results.json).

### 3.4 SQAC: complete reranking, incomplete generated-answer evaluation

The actual upload/hybrid retrieval fixture contains 650 public contexts, 14 files and
939 persisted chunks. The frozen test has 128 questions in 114 article clusters; both
providers scored the same 32 candidates and select eight generation passages.

| Ranking-stage outcome | BGE | Jev | Paired difference and 95% interval |
| --- | ---: | ---: | --- |
| nDCG@8 | 0.844154 | 0.880481 | +0.03632725, [+0.00915534, +0.06706013] |
| Gold-span recall@8 | 0.890625 | 0.898438 | +0.0078125, [0, +0.02419355] |
| Any gold-span hit@8 | 116/128 | 117/128 | +1 query; +0.0078125, [0, +0.02419355] |

Every test query has a gold-span chunk in the corpus, but only 118/128 have one among the
32 retrieved candidates. Ten misses occur before reranking. Of the 118 eligible pools,
BGE retains a gold-span hit in 116 and Jev in 117.

This identifies candidate coverage as a major constraint on the gold-hit outcome:
ten upstream misses versus two BGE last-stage misses. It does not prove that retrieval
is the dominant cause of eventual answer errors, or that ordering has no value.
An absent annotated span also does not prove that every other candidate lacks useful
answer support; reference coverage is a benchmark proxy, not an absolute correctness ceiling.
Jev may improve which evidence appears first; only generated answers can establish
whether that improvement matters under the fixed prompt/context budget.

The 16-question development criterion comparison chose the direct rubric:
nDCG 0.826643399 versus 0.803576509 for the citable rubric. Keep that choice frozen.
The test ranking gain does not satisfy the generated-answer criterion by substitution.

Only one paired generated case completed, with both arms abstaining. Another real
Spanish answer had two bound citations before a harness audit-reader failure.
There is no complete 128-pair answer table or full independent NLI aggregate.
The latest retained attempt stopped at embedding readiness, before upload or paid scoring.

Ranking analysis identities:

- Panel SHA-256: `94adba601b358793ab804b33dba7c5f2db123c5048fe756e056cf09d105a14a3`.
- BGE score SHA-256: `cc3f2f7b116060944ab23bb20ef97104d20d655d2badd498d596a1b60d803bf5`.
- Jev score SHA-256: `fee6c2bfd167f89bfc936290e0830667769f58835d8255911dea5fd9563293b4`.

These values derive from the ignored ranking-stage analysis and are reproduced in
[the previous analysis](continuation-plan-2026-10-02.md).
[Effective protocol](spanish-e2e-protocol.json), [execution record](spanish-e2e.md).

### 3.5 R1, packets and counterevidence: preserve the negative evidence

R1 used local BGE-M3, equal 1,100-source-token budgets and unchanged active chunks/index.
Fixed-leader grouping and re-embedding structural units are different interventions.

| Dataset / complete-evidence micro rate | Existing chunks | Grouping | Re-embedding |
| --- | ---: | ---: | ---: |
| QASPER, 206 eligible questions | 53.40% | 56.31% | 52.91% |
| ContractNLI, 614 positive/contradiction cases | 69.06% | 72.64% | 74.59% |

Equal-document macro differences, not subtraction of the micro rates above:

- QASPER grouping +3.80 pp, CI [−2.12, +9.81]; re-embedding +0.26 pp, CI [−6.52, +6.77].
- ContractNLI grouping +3.33 pp, CI [−0.10, +6.94]; re-embedding +4.89 pp, CI [+1.31, +8.47].

Grouping reduced top-1 evidence intersection in both domains. ContractNLI excluded 423
NotMentioned cases, so the positive result does not test abstention. One-time embedding
timings ran legacy first and are confounded by warm-up/order.

The small EPA probe stayed 4/5 across routes. Eight Jev boundary calls changed no groups;
a later 32-call QASPER boundary probe also changed none. Those probes judge existing
boundaries, not discovery of better alternative cuts.

Packets/counterevidence leave QASPER dense at 53.40%; QASPER TEI goes from 50.97% to
50.49%, losing one complete-evidence case. Equal-paper delta is −0.82 pp,
CI [−2.46, 0]. ContractNLI stays 69.06% dense / 77.04% TEI. These are in-memory
context-selection studies, not qualification of the full database packet path.

A separate RAG_Multilingual transfer set used original human extractive spans, BGE ranking
and a 512-source-token cap: 16 dev and 24 disjoint test cases, half Spanish and half English.
Flat/group/packet/counter routes all reach perfect complete evidence and top-1.
The roughly 6.9% test source-token reduction is a context-size observation, not measured
full-prompt cost or answer quality. This is another ceiling fixture.

**Decision:** do not promote R1, packet expansion, counterevidence or a re-index migration.
The domain-specific ContractNLI signal can justify isolated future research, after local
delivery, with answer/abstention and full prompt budgets.
[R1 report][r1], [packet report][packets], [transfer analysis][transfer].

### 3.6 SciFact: external support scoring is a separate, unqualified feature

Jev Noul judged English expert-labeled support/contradiction using full abstracts,
bypassing retrieval and generation. At the default 0.8 threshold it accepted 12/24
supports and 0/24 contradictions. After inspecting those 48 development cases, a 0.6
cutoff accepted 8/10 supports and 0/10 contradictions on 20 disjoint cases from the
same official development split.

All 68 judgments were valid, but this is not an untouched official test split, Spanish
end-to-end study or calibrated false-support rate. Rejecting zero contradictions in
34 examples does not establish zero future false support. It also suppresses valid
supports. A claim that the citation binder would accept all cases is a structural
counterfactual, not a measured main-pipeline wrong-answer rate.

Keep external strict support off. It does not belong in either accepted extraction.
[Support report][support].

### 3.7 Hybrid/direct smoke: routing and policy can masquerade as model gains

A two-query live hybrid smoke used real app-role PostgreSQL/RLS and authorization,
but seeded synthetic embeddings/test-ready chunks. One boiling-water query produced zero
local hits because of the lexical-share veto and eight Jev hits without that veto;
the seismic query returned the same first source in both arms. This compares policy as
well as scoring. It is not upload/parser/real-embedding/generated-answer evidence.

The ten-query direct-versus-hybrid comparison had identical order on 9/10 and nDCG 0.968
in both paths. Warm medians of 208/207 ms were order-confounded. Removing one source's
embedding proved the direct route could reach an authorized parsed source missing from
the hybrid seven-source result; it did not prove a broadly better search mode.

Do not credit a relaxed lexical gate or changed candidate set solely to Jev.
The frozen SQAC replay checks exact candidate identity/order in both arms, which is the
right constraint for isolating its ranking contribution.
[Hybrid smoke][hybrid], [direct comparison][direct].

## 4. Why the combined evidence does not yet satisfy adoption

The strongest positive historical result is QASPER's fresh 176-paper English confirmation.
The stronger local Spanish comparator changes the picture: Jev's MIRACL gain falls from
0.0407 over mMiniLM to 0.0122 over BGE. SQAC has a larger ordering gain but only one
additional gold-hit case, and generated quality is unavailable.

Four claims therefore need separate evidence:

1. **Engineering correctness:** a typed local boundary or prefix guard works and passes
   the upstream candidate pipeline.
2. **Task quality:** matched Spanish answers are better with valid, supported citations,
   not merely higher-ranked evidence.
3. **Operational value:** whole-query latency, failure/fallback, resource use and
   upload/search contention meet an agreed product budget.
4. **Product permission:** private text may leave the customer's installation, and the
   actual deployment safely enforces processing policy and provider limits.

A win on one claim cannot discharge the others. Low token cost is not permission for egress;
a single-worker public research runner is not a qualified API/worker production deployment.
The process-local quota/breaker is insufficient shared-limit evidence. Inspect actual
call ownership before claiming which processes dispatch provider calls; the presence of
two Compose services alone does not prove concurrent dispatch.

Published human SQAC/MIRACL labels address Martin's objection to implementer-created
ground truth for those outcomes. They do not independently adjudicate every generated
statement or make general Wikipedia QA representative of private Spanish documents.
The independent automatic NLI judge adds useful evidence with an explicit error risk.
No new human-labeling task is required to finish the downloaded-dataset experiment;
Martin decides whether that documented scope is enough to reopen the product discussion.

## 5. Local performance and upload: the measured constraints

### Matched embedding measurements

The CPU/GPU embedding trial used the same BGE-M3 revision, float32, TEI 1.9.4,
four-CPU cap, batch limits 2048 tokens / four items, and one ingestion worker.
Both arms used the same GPU BGE reranker: the CPU-embedding arm is not an all-CPU stack.

| Fixture | GPU embedding upload-to-ready | CPU embedding upload-to-ready |
| --- | ---: | ---: |
| Text, 2,801 bytes | 6.021 s | 3.984 s |
| Text, 144,683 bytes | 44.043 s | 203.932 s |
| Text-layer PDF, 13,371 bytes | 51.544 s | 218.860 s |

New uploads returned 201/pending; duplicates returned 200 with the same document ID.
There were three actual new jobs per trial. These loopback TCP multipart measurements
exclude WAN transfer and OCR. Queue wait includes preceding files; single sequential
observations cannot establish independent per-file speedup distributions.

Twenty queries during ingestion had GPU-embedding median/p95 1.929/5.036 s, no degraded
queries, versus CPU-embedding 5.171/6.432 s and 6/20 degraded. Idle queries reversed
the medians: GPU 1.528 s versus CPU 0.430 s, both without degradation. The recorded p95
implementation selects the maximum for n=20; it is not a stable production tail estimate.

The medium GPU document spent 17.683 s embedding and 19.867 s persisting. Its CPU
counterpart spent 198.137 s embedding and 1.838 s persisting. That reversal means faster
embedding alone does not explain the full path; persistence, batching and host contention
need direct measurement. [Measurements](upload-ready-results.json), [interpretation](followup.md).

### Existing ingestion is substantial; repair the exposed failure

Uploads already stream and hash; deduplication, labels, queue/requeue, parsing,
embedding batches and GPU Compose already exist. Rebuilding them would miss the bottleneck.

The single-file SQAC corpus attempt reached a PostgreSQL statement timeout inserting
939 chunk embeddings, with zero committed output. Splitting the identical corpus into
14 benchmark files completed in 257.365 s and later 234.100 s. That avoided one oversized
insert; it did not fix a user's large-document product path. Both timings are single
local runs. The original corpus reconstruction is 844,643 bytes; uploaded file text totals
844,617 bytes because 26 separator bytes are restored between files.

The existing persistence operation clears prior state and writes pages/chunks/embeddings
within one tenant transaction, then records classifying; ready follows filing.
First test bounded insert/flush groups **inside that transaction**, preserving rollback,
labels, source offsets and readiness order. This reduces oversized SQL payloads without
advertising partially persisted documents as ready. If measurement shows total transaction
duration remains the limit, design a separately reviewed staged-write/recovery change;
do not quietly add commits between batches or raise timeouts to hide the failure.

The independent final-backoff fix `595bbe2e31756b15430a54d225280a596145ac19`
removes the sleep after the last failed attempt: one needless second for interactive
failure and four seconds for terminal ingestion failure. It retains the one-attempt,
five-second query budget and ingestion's three attempts with delays between them.
Its 122 focused passes do not prove contention is solved or qualify a full product merge.

### Effective settings and memory

The existing GPU override changes images/device access, not every profile setting.
Upstream defaults are 2048/4 batches and the worker CLI's
`ZENITH_WORKER_CONCURRENCY` default is one. A recommended GPU profile of 16384/32,
100 candidates, ef=200 and four workers is not evidence that those values are active
or qualified. The SQAC experimental 1024/2 and depth 32 are separate from production
CPU depth eight. Freeze effective environment values for every measurement.

The laptop has an RTX 5070 Ti with about 12 GiB VRAM and approximately 31 GiB host RAM.
Model file sizes are not resident GPU usage. Sequential embed/rerank/generate stages
do not prove simultaneous residency. Llama 3.1's observed fully GPU resident allocation
was about 5.93 GB at 8k context; embedding, reranker, KV growth and other workloads still
need concurrent measurement. Resource aborts below 1 GiB free host RAM are real failures,
not justification for terminating unrelated applications.

### Evaluation infrastructure is currently the immediate research blocker

Recorded embedding readiness was 556.190 s; BGE reranker startup was 693.535 s and a later
restart 555.580 s. The controller's 180-second readiness budget is shorter than those
observations. The latest `run-safe-final` stopped with “Embedding service not ready.”
Increasing a bounded diagnostic budget initially to 900 seconds is justified for recovery;
it is not an acceptable product cold-start claim or a promise that startup will succeed.

Additional retained failures include mismatched client/server batch limits, one-file DB
timeout, UUID-tie candidate changes requiring fresh scores, atomic snapshot read/replace
issues, audit-reader user context omission and memory exhaustion. The audit problem was
in the harness reader; product RLS correctly hid the private log and was not weakened.

The authorized temporary training pause was restored by the watchdog. A CUDA stall during
that attempt does not isolate its cause. Do not resume using OS suspension as routine
benchmark orchestration. Arrange an available GPU window, or record shared-hardware
conditions and withhold isolated latency claims.

## 6. Delivery order and concrete acceptance gates

No research phase is a prerequisite for the two accepted PRs.

### A. Complete the accepted-PR handoff

1. Refresh upstream main and compare the two exact fork heads/parents/trees.
   Reconcile the current draft bodies with already-published branches and retained full-suite
   failures. Include only each extraction's scope and its own checks.
2. Submit two independent PRs to upstream main when executing the publication task.
   Their bodies link old upstream #2/#6 and state that originals remain open.
   No foundation, timing fix, MCP, benchmark, or Jev changes enter either diff.
3. Obtain maintainer fork-Actions approval and inspect actual jobs, including skips,
   for the tested candidate SHA and recorded base/merge SHA. Record the PR URLs and run URLs.
4. If CI fails, inspect the first concrete failure. Compare with the same main baseline
   in that environment. Do not weaken assertions, repeatedly rerun until green, or bundle
   the entire experimental stack. If a genuine baseline timing repair is needed, propose
   the already isolated fix separately.
5. If main advances, prepare new sibling candidates from that current main, preserving the
   published extraction branches and original series. Rerun each composition independently.
6. Give Martin the two short diffs and exact green upstream runs. Leave merging to separately
   authorized maintainer action.

**Done:** two actual independent upstream PRs; verified green required upstream checks for
the final candidate compositions; explicit skipped coverage and replacement mapping.
Approval to run Actions alone is insufficient.

### B. Qualify the existing local GPU configuration before changing defaults

Use the existing Compose override and optional image-only Blackwell overlay. Record image
digest/runtime, `/info`, model revision, precision, worker CLI, batch limits and device.

Run three distinct comparisons so effects remain attributable:

- Same mMiniLM weights, matched serving version/settings, CPU versus GPU.
- Same GPU/runtime/budgets, mMiniLM versus BGE, for quality and resource cost.
- Same BGE-M3 embedding revision/precision, CPU versus GPU, with reranker held fixed.

Measure cold readiness, first request, warmed query latency, resource peaks, fallbacks
and query-under-ingestion behavior. Use repeated runs with balanced order and publish each
run, not just the fastest. Qualify simultaneous model residency with actual requests;
if 12 GiB cannot sustain the stack, measure an explicit local CPU/GPU allocation rather than
claiming sequential demos show it fits.

**Done:** reproducible measurements separating device/model/runtime changes; no quality
regression on unchanged fixtures; documented deployment memory fit and measured latency
distribution. Agree numeric production latency/resource budgets with Martin before treating
any locally chosen number as an acceptance contract.

### C. Fix large-document persistence, then measure contention

**First product increment:** bound persistence insert groups without changing the
transactional visibility contract. Reproduce the actual 939-chunk failure and compare
identical input before/after. Check chunk/vector counts, source coordinates, labels,
classification/ready order, rollback after a middle-group failure, and retry idempotence
under the application role. Preserve dedup document identity.

Instrument upload acknowledgment, enqueue, queue wait, parse/chunk, embed, persist,
classification and ready. Report per-job sizes/tokens/chunks and host/GPU/DB resources.
Capture relevant statement and lock timings; avoid turning source text or credentials
into telemetry.

**Second increment, only if measurements justify it:** reduce interactive/ingestion
contention using existing worker/service controls. Start with effective concurrency one;
change one control at a time. Do not mistake an in-process semaphore for coordination
between API and worker processes. Offload parser work only after measuring event-loop
blocking; do not introduce a general scheduler platform.

Include queued cancellation, crash/requeue, duplicate upload with label changes and revoked
upload permission. Keep one oversized-document test; file-splitting solely in the fixture
cannot count as a product fix.

**Done:** the original large document reaches ready reliably, failure leaves recoverable
state without partial ready exposure, and repeated foreground/background trials disclose
both latency and degraded-query rates. No timeout inflation or new database is required
as the first intervention.

### D. Finish the local MCP consumer; keep intranet optional

Implemented local stdio head:
`5f590bb3f1ca24e4e20dafb2ee995636ab25f7eb`.
Optional authenticated branch `feat/mcp-intranet-auth` head:
`f344b008fa9543ba8b132de21bcd8515603b8930`.

The local branch's full backend result is 911 passed / 12 skipped; the authenticated branch
has 927 passed / 13 skipped. The final real Keycloak 26.8 PKCE/current-authority/logout
proof passed in 20.10 s. These are separate local branches and loopback proofs, not
upstream acceptance or a production deployment.

Reuse the pinned MCP SDK 2.2.0/protocol 2026-07-28 and the local reference client/model.
The next consumer step is to select and test an actual local interactive host using the
documented tool contract. Measure discovery, cancellation, source authorization refresh,
revocation, cited-source recheck and errors. Pin the host version; “MCP compatible”
does not qualify every consumer.

Keep binary upload in the trusted client using authenticated streaming REST multipart.
The model receives bounded status/source information, not base64 files or arbitrary
filesystem access. Test user file selection and original-file hash through that actual
consumer, as well as pending/duplicate/ready/error display. REST dependencies do not
automatically authorize a direct MCP service call; retain explicit permission checks and
application-role RLS.

For intranet, retain self-hosted Keycloak as the existing implemented proposal. Qualify issuer,
TLS/DNS, audience/scopes, expiry/revocation, explicit identity enrollment and deployment
ownership before rollout. Do not invent those missing inputs or call loopback PKCE proof
a production installation. Web HS256 tokens without MCP audience/scopes are not a complete
HTTP MCP authorization boundary.

**Done for local MCP:** a pinned actual consumer works with local model, authenticated
upload, cancellation and current-user source access, with no cloud processing or private
content in traces. Intranet rollout is a later gate.
[Decision record](mcp-decision.md), [local evidence](continuation.md),
[authenticated follow-up](followup.md).

## 7. Separate research plan: finish the existing experiment before expanding it

### R0. Repair the runner without further paid calls

Follow the earlier continuation plan's implementation checklist:

- Configurable bounded 900-second initial model readiness with identity and neutral request
  checks; resource sampling begins before model startup.
- Immediate durable phase/error records and diagnostics; preserve the previous failed runs.
- Cleanup owned children/services even when failure precedes pytest creation.
- Propagate pytest's nonzero exit from `docker_checks.py`, while retaining the structured
  report checks.
- Keep one isolated existing PostgreSQL database/run ID across upload, capture, scoring and
  query stages. Preserve document IDs/candidate order on resume; do not recreate UUIDs and
  silently treat changed pools as old cached scores.
- Prove one development/public smoke upload, Spanish response, citation binding and
  author-scoped audit read, plus interrupted-stage resume and owned-process cleanup.

**Gate:** deterministic local smoke/resume and failure exits. No missing-stage success
markers, orphan services or paid replay. This is a harness repair, not a new vector store.

### R1. Complete all frozen paired answers and offline grading

Freeze the existing 128 IDs, 114 clusters, 16 development cases, original/effective
protocols, generator digest, production prompt, direct Jev rubric, 32-to-eight candidate
policy and all shared context/output limits. Cache reuse requires exact question, full
passage text, file/coordinates and current ordered candidate identity. A new pool requires
documented independent scoring, not label-informed candidate substitution.

For every case retain both arms' actual `/query` answers and:

- Reference/span match, each citation's authorized source identity/coordinates and bound text.
- Sentence citation coverage and independent local NLI entailment for the cited evidence.
- Spanish-language behavior, abstention, truncation, malformed output and audit success.
- Execution failure/fallback and whether generation was completed.

The primary outcome is `entailed_grounded_reference_match`: reference-match proxy plus
the fixed citation/support conditions. Report exact-match's paraphrase blind spot and
NLI's errors. Keep reference-only and each citation/NLI component as diagnostics.
Reference matching can favor literal extraction over a correct paraphrase; valid citation
IDs can still point to irrelevant evidence. Publish those component failures rather than
treating a citation marker as support. If the automatic judge needs broader qualification,
use existing independently labeled Spanish NLI examples outside this panel; two neutral
sanity probes are insufficient. Do not recalibrate the frozen 0.8 cutoff on test outputs.
An English canned abstention already observed remains a language defect; do not translate
it after the fact to improve this frozen run. Propose localization separately.

Use 2,000 paired article-cluster bootstrap resamples, seed 20261002. Publish:

- Meaningful generated-answer gain: mean at least +2 percentage points, lower CI above zero.
- Clearly larger gain: mean at least +5 points, lower CI at least +2 points.
- All paired wins/losses/ties and exclusions, not just a percentage.
- Operational completion/failure over all 128 selected cases; no silently dropped failures.
- Explicit incomplete status if any paired answer or independent grade is missing.

These are generated-answer thresholds, not MIRACL/SQAC nDCG thresholds. Do not lower a gate
after observing the result, retune the held-out prompt, swap to a weaker comparator, or
search rubrics until this panel produces the desired result.

This staged functional REST pipeline verifies real ingestion, hybrid candidates, audit/RLS,
local generation and citations. It does not establish concurrent online Jev latency,
multiuser throughput, desktop MCP tool-selection quality or production readiness.

**Gate:** complete 128-pair artifacts, complete independent grading, frozen-method report
and uncertainty. A positive result reopens research discussion, not automatic product adoption.

### R2. Diagnose the error stage before funding another comparison

On the completed panel, describe failures by stage: candidate miss, selection/order,
reference/paraphrase, unsupported claim, citation identity, abstention, language and
execution. The existing 128 are now an analysis panel, not a fresh tuning/confirmation set.

Use development data for any candidate-depth, hybrid fusion, query rewrite, local model,
rubric or context-budget change. Test local alternatives before additional paid scoring.
Then freeze a new genuinely unexamined question/article-family holdout, disclose previously
inspected overlap and compare matched arms once. Remaining questions in a downloaded file
are not automatically an independent holdout if their families or labels were inspected.

Include multilingual/Spanish domain cases with independently published evidence where
available: multi-evidence answers, near-duplicate versions, dates/numbers and legitimate
unanswerable questions. Do not manufacture noisy hard negatives or automatically generated
legal answers and relabel them as expert gold. Generic SQAC/Wikipedia success is not proof
of private legal/administrative correctness.

Downloaded ALIA legal/admin CQA answers are synthetic; the downloaded triplet evaluation
has 11,059 rows and lacks hard-negative fields. It can exercise loaders and domain retrieval,
but cannot satisfy Martin's independent-label quality requirement by itself.
The human extractive RAG_Multilingual transfer sample already saturates; simply making that
perfect fixture larger does not guarantee a discriminating test.
Dataset provenance, revisions, file hashes and attribution remain in
[the Spanish manifest](spanish-data-manifest.json).

**Gate:** a declared new held-out protocol with evidence provenance, balanced candidate
and generator budgets, and no model-based label claims disguised as independent judgment.
If no suitable independent domain labels exist, state that limitation rather than claiming
the existing public test qualifies the customer corpus.

### Research budget and privacy

The latest authorized family combines MIRACL and SQAC attempts:
14,901 successful Jev calls / $0.378251202 accounted input cost:

- MIRACL: 5,173 / $0.113911056.
- SQAC attempts: 9,728 / $0.264340146.

Both caps apply: 100,000 calls **and** $5, leaving at most 85,099 calls and $4.621748798
before any additional reservations. These are reported token-rate estimates, not an invoice.
Historical September pilot/QASPER/support authorizations are separate; 14,901 is not
the lifetime project call count. Uncertain in-flight/reserved outcomes must remain reserved.

No new calls were made for this analysis. Finishing grading of existing scores needs no
new Jev inference if exact pool identities can be retained. A large remaining allowance
is not a target to spend.

Send only exact approved public fixture question/source spans; keep labels out of provider
inputs and keep credentials out of tracked files, report text and child processes that do
not need them. Private datasets, raw completions, model weights and detailed local logs stay
ignored. Paid public research does not authorize customer-text processing.

## 8. Decision table after the next measurements

| Observation | Action | Claim that remains unavailable |
| --- | --- | --- |
| Both extraction PRs have green upstream CI | Ready for Martin's code review | No Jev adoption or automatic merge |
| Same-weight GPU comparison improves latency without quality loss and fits deployment | Propose a small local configuration rollout with measured limits | No universal CPU/GPU speedup |
| Bounded persistence repairs the oversized-document failure | Submit a focused ingestion fix with failure/recovery evidence | No broader throughput guarantee without contention trials |
| Actual local MCP consumer passes access/upload/citation checks | Present the local client integration for review | No arbitrary cloud client or intranet rollout qualification |
| Frozen Spanish primary gain is absent or uncertain | Keep the local baseline; publish the outcome and stage diagnosis | No reranker superiority claim |
| Spanish primary gain passes the meaningful gate only | Describe a bounded benefit on that fixture | No “far above threshold” or private-domain claim |
| Spanish primary gain passes the larger gate | Request Martin's review of the frozen evidence and its scope | Egress and topology objections still stand |
| Quality wins but latency/privacy/topology do not meet product constraints | Retain Jev as public research | No production enablement |
| New domain fixture has only synthetic labels or ceiling results | Use it for functional smoke and disclose limits | No independent enterprise quality acceptance |

A fair experiment can establish that Jev wins or that it does not. The plan optimizes
Zenith's product and the quality of the evidence; it cannot promise a particular winner.

## 9. Deliverables and handoff

Priority order:

1. Two short independent upstream PR submissions and exact candidate CI records.
2. Local GPU identity/memory/latency qualification and a focused persistence reliability fix.
3. A pinned actual local MCP consumer; intranet deployment inputs recorded separately.
4. Runner smoke/resume repair and the complete frozen Spanish answer/citation report.
5. New domain research only after the frozen outcome and failure-stage diagnosis.

These streams can progress independently. Waiting for maintainer CI approval need not stop
local persistence or runner work; research must not hold the accepted PRs hostage.

Each code proposal should have one upstream-main base, an exact head/tree, a small diff,
actual command/exit/skip records, retained failures and rollback/deployment scope.
Preserve original branches and PRs. If future integration is authorized, qualify that
new combined composition rather than borrowing checks from its separate ingredients.

For the eventual maintainer summary, communicate these facts plainly:

- The requested local slices are independent and have no Jev/foundation prerequisite.
- The exact upstream CI state is linked; local full-suite failures remain visible.
- Same-weight local GPU and ingestion measurements are reported with contention limits.
- MCP starts with the selected local model/client and authenticated streaming uploads.
- Spanish Jev ranking improved, but generated-answer superiority remains unproven until
  all 128 pairs are completed and independently automatically graded.
- Private egress and deployment safety remain separate product decisions.

This is a draft handoff, not a message sent to Martin. The analysis does not close, modify,
merge or publish any existing PR, and it does not change the current product defaults.

## Sources and evidence boundaries

Historical report links below are pinned to the preserved report branch commit
`7c4af947617d08eecf0f4b9798b033910512d770`, except the 40-case QASPER and broad R1
reports, which reside on the preserved research branch commit
`0d0844ba236a08d4983bfc93cb98b76ab0497406`. Neither branch is current upstream.
Current local records linked above retain their own test commits and incomplete runs.
Live CI links identify the actual observed runs, not inferred success.

[pilot]: https://github.com/Kripta-Studios/zenithEnterprise/blob/7c4af947617d08eecf0f4b9798b033910512d770/backend/eval/reports/evidence-v3-public-2026-09-25.md
[qasper40]: https://github.com/Kripta-Studios/zenithEnterprise/blob/0d0844ba236a08d4983bfc93cb98b76ab0497406/backend/eval/reports/evidence-v3-qasper-judge-live-2026-09-26.md
[qasper240]: https://github.com/Kripta-Studios/zenithEnterprise/blob/7c4af947617d08eecf0f4b9798b033910512d770/backend/eval/reports/evidence-v3-qasper-heldout-2026-09-27.md
[qasper176]: https://github.com/Kripta-Studios/zenithEnterprise/blob/7c4af947617d08eecf0f4b9798b033910512d770/backend/eval/reports/evidence-v3-qasper-extension-2026-09-27.md
[r1]: https://github.com/Kripta-Studios/zenithEnterprise/blob/0d0844ba236a08d4983bfc93cb98b76ab0497406/backend/eval/reports/evidence-v3-r1-broad-2026-09-26.md
[packets]: https://github.com/Kripta-Studios/zenithEnterprise/blob/7c4af947617d08eecf0f4b9798b033910512d770/backend/eval/reports/evidence-v3-packets-2026-09-26.md
[transfer]: https://github.com/Kripta-Studios/zenithEnterprise/blob/7c4af947617d08eecf0f4b9798b033910512d770/docs/evidence-v3-hardening/r1-packets-analysis.md
[support]: https://github.com/Kripta-Studios/zenithEnterprise/blob/7c4af947617d08eecf0f4b9798b033910512d770/backend/eval/reports/evidence-v3-scifact-support-2026-09-26.md
[hybrid]: https://github.com/Kripta-Studios/zenithEnterprise/blob/7c4af947617d08eecf0f4b9798b033910512d770/backend/eval/reports/evidence-v3-public-2026-09-25-live-hybrid.md
[direct]: https://github.com/Kripta-Studios/zenithEnterprise/blob/7c4af947617d08eecf0f4b9798b033910512d770/backend/eval/reports/evidence-v3-public-2026-09-26-direct-hybrid.md
