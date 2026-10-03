# Completed Spanish generated-answer and citation comparison

Product-decision update, 2026-10-03: the user has authorized offering Jev reranking for
approved private corpora in this fork. See [the adoption rationale and processing boundary](jev-private-corpus-decision-2026-10-03.md).
That decision supersedes the earlier recommendation against a private pilot, while the
measured results, uncertainty, gate limitation and separate upstream acceptance remain unchanged.

Date: 2026-10-03. Research branch: `perf/spanish-e2e-citations`.
Actual pipeline tested at `2c563142db1551ef5eb68174b23694a2a8af5fb2`.

**All 128 paired test questions completed through the actual authenticated Zenith query,
citation-binding and audit path. All 256 arm outcomes, including abstentions, then received
independent automatic entailment grading. Jev passes the meaningful-gain criterion but
fails the preregistered clearly-larger-gain criterion. The dominant newly measured
limitation is the local relevance gate, followed by generated-claim support. Keep local
processing as the product direction.**

This report supersedes the incomplete-run status in [the evaluation design](spanish-e2e.md)
and [the previous model analysis](martin-acceptance-and-model-analysis-2026-10-03.md).
Their historical failures and measurements remain available. The aggregate
[JSON](spanish-e2e-results-2026-10-03.json) contains exact values, intervals, model pins,
input hashes and integration-test identity. The [128-row CSV](spanish-e2e-cases-2026-10-03.csv)
contains paired scalar diagnostics without questions, document text or completions.

## Completed cohort and primary result

Published SQAC human answer spans supply independent reference labels. Selection remained
128 questions from 128 test contexts, grouped into 114 article clusters; 16 disjoint
development contexts selected the Jev rubric. All 650 corpus contexts were uploaded.
Both arms received the same 32 real hybrid candidates and selected eight passages.
No gold candidate was inserted, no unsuccessful question was excluded, and no rubric,
generator option, relevance gate, citation criterion or NLI threshold was retuned on test
results.

The primary metric requires reference-answer containment, a bound citation whose source
range contains that reference, sentence citation coverage and independent entailment
probability at least 0.8 for every answer sentence. Abstentions score zero. It is an
explicit automatic proxy rather than comprehensive semantic accuracy.

| Measure, denominator 128 | BGE GPU | Jev | Jev minus BGE, paired 95% CI |
| --- | ---: | ---: | --- |
| Primary: reference, citation and all-sentence NLI | 10/128 = 7.8125% | 20/128 = 15.6250% | +7.8125 pp [1.5504, 14.7287] |
| Reference and citation, before independent NLI | 26/128 = 20.3125% | 49/128 = 38.2813% | +17.9688 pp [9.5238, 26.2295] |
| Reference-answer containment | 33/128 = 25.7813% | 56/128 = 43.7500% | +17.9688 pp [9.8361, 25.9843] |
| Answer token F1 | 0.157917 | 0.317540 | +0.159623 [0.098315, 0.223422] |
| Retrieval nDCG@8 | 0.844154 | 0.883364 | +0.039211 [0.013231, 0.069050] |
| Gold-span recall@8 | 0.890625 | 0.898438 | +0.007813 [0, 0.024194] |
| Answers delivered | 42/128 | 74/128 | +32 answers; this is coverage, not accuracy |
| Abstentions | 86/128 | 54/128 | -25.0000 pp [-34.0909, -16.1290] |

Intervals use the frozen paired article-cluster bootstrap: 2,000 resamples, seed 20261002.
The meaningful criterion, mean gain >=2 pp and lower bound >0, **passes**. The clearly
larger criterion, mean gain >=5 pp and lower bound >=2 pp, **fails** because the primary
lower bound is 1.5504 pp. Doubling a low 7.8125% primary baseline does not establish high
absolute reliability. The span-only gain cannot replace the primary result.

Paired primary outcomes are seven successes in both arms, thirteen Jev-only successes,
three BGE-only successes and 105 failures in both. These counts retain every test case.

## Why the observed gain needs a local admission-control comparison

The existing relevance classifier rejects a shortlist when fewer than one third of its
hits have a lexical rank. It also rejects a best rerank score below 0.02. Both arms used
these unchanged rules. This experiment did not recalibrate the score floor for BGE or
Jev; the product's configured reranker remains mMiniLM. Neither rank scores nor their
absolute calibration are interchangeable merely because both fall in [0, 1].

| Actual funnel | BGE | Jev |
| --- | ---: | ---: |
| Top-32 candidate pool contains an annotated answer chunk | 118 | 118 |
| Selected top-eight contains an annotated answer chunk | 116 | 117 |
| Lexical-share veto | 83 | 52 |
| Lexical veto despite annotated evidence in selected eight | 75 | 47 |
| Score below 0.02, including lexical overlap | 8 | 0 |
| Score-floor veto without lexical veto | 2 | 0 |
| Abstained before generator invocation | 85 | 52 |
| Generator invoked, including identical-prompt reuse | 43 | 76 |
| Abstained after generator invocation | 1 | 2 |
| Delivered answer | 42 | 74 |
| Primary success | 10 | 20 |

**Eleven of the thirteen Jev-only primary successes occur where the lexical gate stopped
BGE before generation.** Only two Jev-only primary successes occur where both arms reached
generation. Among the 38 cases where both arms invoked the generator, BGE passes eight
and Jev nine. That subset is selected after treatment; its 8/38 versus 9/38 comparison is
diagnostic, not an unbiased causal estimate.

The complete end-to-end gain is real under this frozen configuration, but much of its
advantage is consistent with ranking interacting with lexical admission. Correct source
availability differs by only one case in the selected eight, while answer coverage differs
by 32. Seventy-five blocked BGE cases with correct evidence are potential local recovery
opportunities, not 75 promised counterfactual successes. The generator and independent
judge can still reject them.

Ten candidate pools lacked an annotated answer chunk before either reranker; neither
provider can repair this retrieval ceiling by permutation. This is another distinct
failure family. Because SQAC's selected questions are answerable, this study does not
measure false answers on unanswerable or out-of-domain questions. Disabling the relevance
gate without that control would be an unqualified product change.

## Citations, generated claims and Spanish language

Both arms have zero invalid bound citations and zero fabricated raw numeric markers.
Those are identifier/span-binding checks. They do not establish that each claim follows
from its cited text. All-sentence citation coverage holds in 38 of 42 BGE answers and
70 of 74 Jev answers. The stricter reference/citation metric passes 26 and 49 answers;
independent NLI reduces those to ten and twenty. Sixteen BGE and twenty-nine Jev
reference-and-citation successes fail the independent entailment requirement.

The judge checked 58 BGE claim sentences and 103 Jev sentences; sixteen and thirty-six,
respectively, exceed its fixed 0.8 entailment cutoff. Entire answers satisfy the
all-sentence entailment condition in thirteen BGE and twenty-four Jev cases, including
answers which do not satisfy the reference-span metric. Six BGE and twelve Jev claims
needed overlapping source windows, with a maximum of two. There was no silent source
truncation.

The independent local classifier receives only a claim and its bound cited text, without
provider identity, rank score or reference labels. Its unrelated Spanish sanity
probabilities were 0.997708 for the supported example and 0.010115 for the unsupported
example. Two sanity examples verify basic operation; they do not calibrate an entire
Spanish QA domain. A rejected claim may reflect a real support problem, incomplete citation
context or a classifier error. This experiment does not equate NLI failure with proven
hallucination, nor does it supply independent human adjudication of every generated claim.
Published human references and independent automatic claim grading satisfy the requested
automatic evaluation; they do not replace that distinction in Martin's review.

The actual local generator produced Spanish answers using the existing prompt. All 86 BGE
and 54 Jev abstentions retain the product's English canned response. They were not
translated after execution and are counted as failed primary outcomes. This is a measured
localization defect. The run does not claim that every returned HTTP answer string was
Spanish or introduce an unregistered language-accuracy score.

## Models, hardware and execution boundaries

| Role | Fixed identity |
| --- | --- |
| Embeddings | BGE-M3, revision `5617a9f61b028005a4858fdac845db406aefb181`, TEI 1.9.4 float16 |
| Local reranker | BGE-reranker-v2-m3, revision `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, TEI 1.9.4 GPU float16 |
| External research reranker | `jev-1.13.0`, frozen Spanish direct-answer rubric selected on development only |
| Generator in both arms | `llama3.1:8b-instruct-q4_K_M`, digest `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` |
| Independent automatic judge | `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`, revision `8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c`, local CPU float32 |

Generation used temperature zero, seed 20261002, context 8192, output limit 256 and
thinking disabled. Maximum observed prompt counts were 3150 BGE and 3190 Jev. One BGE
and three Jev completions reached the output limit; they remain included. Three BGE and
six Jev generator invocations reused an identical full prompt's original completion.
Generator preflight confirmed full GPU residency; the optional partial-residency switch
was not used.

The successful shared-hardware readiness window required six stable samples with at
least 2500 MiB host RAM free, 3000 MiB VRAM free and background GPU utilization <=85%.
The unchanged default gate is more conservative. The generation monitor recorded 323
samples, with minimum free host RAM 2566.434 MiB. This tight margin further limits any
simultaneous-stack claim. BGE neutral readiness took 181.703 seconds, within the new
900-second deadline; embedding readiness was a warm 0.781-second check.

The rejected cached Qwen3 tag's thinking-only readiness failures remain historical
execution evidence; it was not a scored test arm. mMiniLM was evaluated in the earlier
MIRACL ranking study, not as a generated-answer arm here. Historical Score6, packets,
QASPER and SciFact results remain in the deeper model analysis; these 128 comparisons
do not retroactively qualify those providers or English fixtures.

Execution used a shared RTX 5070 Ti Laptop GPU, about 12 GiB VRAM, and about 31 GiB host
RAM. Real embedding/retrieval capture, reranking and local generation ran in separate
model stages. Each generated query reran retrieval against the same persistent isolated
database and checked full candidate identity, order and metadata before score replay.
All 144 development/test captures survived the resume check. The authenticated query path
then ran actual generation, citation binding and author-scoped audit assertions. This is
a functional end-to-end comparison; it is not simultaneous online cloud latency, an
interactive MCP-client test or proof that the full three-model stack fits concurrently.
No unrelated training process was suspended or stopped during this completed attempt.

The final successful pipeline ran all 128 pairs in 943.254 recorded pipeline seconds.
Pytest reports **1 passed in 963.67 s**; the Docker-check wrapper records **983.86 s** and
exit zero. Those clocks have different scopes. Original-completion median generation
times, 3.228 s BGE and 2.924 s Jev, use different admitted question sets and exclude live
external reranking from the query replay. They are not a fair whole-query speed comparison.

## Actual upload measurement, recovery and paid accounting

The first persistent upload stored fourteen new files, 844,617 bytes and 939 chunks;
upload-to-ready was **199.385 seconds**. The complete reconstructed corpus is 844,643
bytes, including 26 bytes of inter-file separators. Resume uploads reused the same
document IDs via normal deduplication. The 199.385-second observation is the original
new-document measurement, not duplicate-upload readiness or an ingestion SLA.
The embedder was prewarmed; its subsecond resumed health check is not cold startup.

The large single-file embedding INSERT timeout remains product backlog. Splitting the
benchmark input at existing context boundaries preserved the corpus but did not fix that
product bottleneck. Existing streaming upload, deduplication, queued ingestion, TEI batch
planning and GPU Compose infrastructure were reused.

The completed run recovered from two retained failures: the first persistent attempt
completed ten pairs before repeated test logins hit the unchanged login rate limiter;
the next resume failed reading a Spanish Windows path with the locale's default encoding.
The harness now uses normal refresh-token rotation and explicit UTF-8 JSON reads. Product
rate limits, tenant policies and citation writers did not change. The coordinator now
keeps an explicitly owned isolated database across attempts, bounds model readiness,
requires real neutral inference and propagates Docker test failures. It revalidates the
frozen capture and complete scoring matrices before reuse.

Of 4608 development/test question-passage pairs per arm, 4334 matched successful prior
scores exactly by question, filename, character range and passage text. Both providers
scored the remaining 274 pairs. The new Jev calls cost an estimated **$0.007437990**;
no new paid requests were issued for the successful resume, generation or NLI stage.
The latest authorized study family totals **15,175 calls / $0.385689192**: MIRACL
5173 / $0.113911056, prior SQAC attempts 9728 / $0.264340146 and this recovery
274 / $0.007437990. This is not the lifetime call count of every historical experiment.

The user's cumulative limits remain 100,000 calls and $5. Input-token accounting uses
the [official model price](https://docs.typesafe.ai/models), checked 2026-10-03:
$0.042 per million input tokens for `jev-1.13.0`, with output tokens free. The estimate
is not a billing invoice. Unknown request outcomes stay reserved rather than being
automatically retried. Only the frozen public research inputs were eligible for dispatch.

## Checks, provenance and reproduction

The actual opt-in Linux integration check passed at the head named above, tree
`11e7a8939e36da1d5d430f1aa12d3420b1f96163`, runner image
`sha256:906ce21d27968f6b2ec1d5d83601bec84f875d74bef5cbfaf8eafee948458d88`:

```text
uv run python -m pytest -q --tb=short eval/tests/test_spanish_e2e_pipeline.py
1 passed in 963.67s (0:16:03)
```

Seven runner regressions and twelve existing metric/citation/entailment checks passed.
The changed pipeline module passed strict Linux-target pyright with its actual dependency
interpreter; changed Python files passed Ruff. These checks qualify the research runner,
not upstream CI for the two independent engineering extractions.

The final candidate panel SHA-256 is
`f189be892b735ae1ff1e68570a80adec5fbfa34e797dc78a13fed88f9c175ab5`.
NLI binds the exact generated-result input hash
`f044f3cc8093d1f4738c3c56e59c4225b01445e29cc0c39f42faa11cb0386642`.
Raw aggregate summary hash is
`e7b67af53cf012ab92fb0bfb18f7c117051bfdf154bb171a4063cafd41328aa6`.
The complete checked artifacts' hashes are in the public JSON. The previous ranking-only
panel has a different identity; its Jev 0.880478 nDCG value must not replace this panel's
0.883364 measurement.

Ignored local evidence is under `.local-evidence/e2e/run-complete-20261003`; per-attempt
snapshots retain failures, original uploads, model readiness, paid ancestry and resource
logs. Model weights and raw public datasets remain local. Export the aggregates with:

```powershell
python scripts/local-first/export_spanish_e2e_evidence.py --run .local-evidence/e2e/run-complete-20261003 --output docs/local-first
```

The exporter refuses incomplete grading, changed responses/shortlists, duplicate query
IDs, degraded outcomes, mismatched input hashes or a failed integration check. It exports
only scalar diagnostics, aggregate protocol and provenance. The full coordinator and
dataset preparation instructions remain in the evaluation design.

The final evidence commit also sorts the pipeline's imports to satisfy Ruff; it does
not alter the functionally tested pipeline behavior. The integration head above remains
the exact commit used for the measured full run.

## Next work, aligned with Martin's product decision

1. **Deliver the independent judge and proxy changes through upstream review and CI.**
   Use their existing standalone branches, each directly based on upstream main. Their
   own exact candidate checks and maintainer-approved Actions remain required. This
   research branch is not either accepted extraction. Preserve the original fifteen PRs
   and all existing branch histories; do not merge or close them automatically.
2. **Qualify a local relevance-gate correction before claiming provider superiority.**
   Evaluate shortlist-level lexical evidence versus evidence in the pre-rerank pool,
   rather than letting eight reordered lexical tags veto otherwise supported answers.
   Calibrate score admission per local model on development data. Include answerable,
   unanswerable, keyword, accent, out-of-domain and tenant-isolated controls; retain safe
   abstention behavior. Compare configured mMiniLM and BGE, then freeze a new policy and
   measure it on unseen article families. The exposed 128 questions are diagnostic data,
   not a fresh blind confirmation set. Do not silently change this completed run.
3. **Measure claim support and Spanish failure messages.** Fix localized canned
   abstentions separately. On independent development examples, assess classifier
   false rejections, citation-context completeness and output-length failures. A local
   generator/prompt improvement must keep source binding and be evaluated with the same
   independently frozen judge on fresh held-out questions. More unsupported output is
   not an improvement merely because it raises answer coverage.
4. **Fix large-document persistence and measure upload under active querying.** Reuse
   streaming/dedup and existing batch planning. Bound database embedding inserts without
   loosening RLS or papering over timeouts. Recheck atomicity, worker recovery, duplicate
   uploads and cancellation, then run multiple size/concurrency trials and report
   upload acknowledgement, queue wait, embedding, persistence and query p95 separately.
5. **Qualify the selected local-model MCP consumer and complete deployment evidence.**
   Exercise an actual client through local stdio, citations, upload compatibility,
   cancellation and private-document isolation. Keep the optional intranet identity
   decision separate; the loopback Keycloak proof is not production TLS or identity
   qualification. Measure simultaneous local GPU services and resource contention.
6. **Revisit Jev only with the corrected local comparator and fresh evidence.** The
   present result is a meaningful configuration-level gain, not a clearly-large gain
   or authorization for private-document egress. Martin's privacy decision and the
   unqualified multiworker quota/breaker topology remain independent blockers to product
   adoption. No distributed Jev quota system, new vector database, general agent platform
   or product Jev enablement is part of this delivery.
