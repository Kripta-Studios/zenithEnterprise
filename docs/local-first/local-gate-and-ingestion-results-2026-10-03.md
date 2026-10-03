# Fresh Spanish relevance-gate validation and single-file ingestion

The candidate-level lexical correction passes its frozen admission/retrieval criterion
on 128 previously unused SQAC article families. Correct evidence in the selected eight
is admitted for 113 questions rather than 32. The original 650-context corpus also
reaches ready as one 844,643-byte document, without the earlier fourteen-file workaround.
Both independent production branches have full green fork CI; Martin's two requested
upstream slices separately have full green upstream CI and await his review.

This is a local BGE retrieval/admission experiment, not a second generated-answer
comparison. It made zero Jev calls and zero generation calls. The earlier complete
128-pair Spanish cited-answer study remains the generated-answer evidence.

Machine-readable results: [JSON](local-gate-and-ingestion-results-2026-10-03.json),
[source-free case CSV](local-gate-and-ingestion-results-2026-10-03.csv),
[frozen protocol](local-gate-protocol-2026-10-03.json).

## Fresh cohort and fixed decision rule

Selection was committed before model scoring, using seed 20261003. Exclude all 130
article-family hashes used by the old fixture, including development cases. Select
one published question per 128 previously unused SQAC families by stable hash order,
with their human-authored reference answer spans. An independent check of both raw
fixtures found zero article-family overlap and zero question-ID overlap.

The corpus is the exact original 844,643-byte text, SHA-256
`b1b7d0a5fc83e081b5e7bf141af74d1e41e47c635807f68adcf5f4ca9715263d`.
Upload it as `sqac-full.txt`. Thirty-two additional source documents contain the
contexts of published impossible questions from Spanish SQuAD v2. Their labels are
not created by this implementation: each published question has `is_impossible=true`
and an empty answer list. The Spanish text is automatically translated, however;
these are not independently human-adjudicated Spanish generated-answer claims.

Each negative query is restricted through the real `documents` search parameter
to its own uploaded source document. The captured candidates were checked to remain
inside that scope. This supplies unanswerable-in-source controls, not a test of
unrestricted out-of-domain queries against the entire collection.

Dataset provenance:

- [PlanTL-GOB-ES/SQAC](https://huggingface.co/datasets/PlanTL-GOB-ES/SQAC), revision
  `f9928e8819596a601b8887cc5f8598b15d589a82`; test-file SHA-256 is recorded in the protocol.
- [TheTung/squad_es_v2](https://huggingface.co/datasets/TheTung/squad_es_v2), revision
  `c9a3b59be01a1e11493e9830e2d7920f72d6dc77`; `dev-v2.0-es.json` contains 11,858
  questions, of which 5,930 are marked impossible. Its file hash is in the protocol.

The production change reads lexical share from the permission-scoped hydrated
candidate pool before reranking. It still reads the best rerank score from the
returned shortlist. The lexical floor remains one third, the score floor 0.02 and
the weak band 0.15; no thresholds were tuned to this cohort. The no-reranker path
retains its previous behavior. No search permission, label or tenant rule is relaxed.

Both measured rules use the same actual query embedding, retrieved candidates,
scores and selected eight passages. Only the lexical denominator changes. The
predeclared criterion is at least five percentage points more gold-evidence admission,
with no increase in negative admission. Two thousand paired article bootstrap
resamples provide the 95% interval; here each positive question has its own article.

## Exact measured result

| Outcome | Previous gate | Candidate gate |
| --- | ---: | ---: |
| Queries with annotated evidence in selected eight | 117/128 | 117/128 |
| Queries admitted | 33/128 | 119/128 |
| Admitted with annotated evidence in selected eight | 32/128 (25.00%) | 113/128 (88.28%) |
| Scoped impossible controls admitted | 31/32 | 31/32 |

Gold-evidence admission improves by 63.28125 percentage points, with paired 95%
interval [54.6875, 71.875]. There are 81 new-only gold admissions and zero old-only
gold admissions. No negative control switches from refusal to admission, or the
reverse. The frozen acceptance criterion passes.

The control result is a substantial remaining weakness: both policies admit 96.875%
of these impossible queries. Keeping that number unchanged does not establish good
abstention behavior. Lexical match plus relevance score is not answerability. Nor
does correct evidence among eight passages guarantee a correct generated answer.
The next quality bottleneck is supported-answer selection and abstention, not simply
allowing more queries to reach generation.

This also strengthens the earlier confounding diagnosis. The old Jev/BGE difference
was measured with a gate that rejected many useful BGE shortlists. The correction
does not erase that historical result, but a claim that Jev remains intrinsically
superior requires a new paired generated-answer comparison against the corrected
local path. Do not extrapolate 113 evidence admissions into 113 successful answers.

## One original corpus file through actual upload and worker

The measured path uses authenticated TCP upload, streaming storage and deduplication,
the existing ingestion queue, a single worker, real pinned BGE-M3 GPU embeddings,
application-role PostgreSQL/RLS, classification and ready-state verification. The
new production code bounds embedding INSERT flushes to groups of 64 inside one
transaction. It does not raise statement timeouts, change models, weaken isolation,
commit partial documents or introduce another vector database.

| Measurement | Result |
| --- | ---: |
| Original single-file payload | 844,643 bytes |
| Original document chunks | 938 |
| Original document ingestion | 164.229 s |
| Original document persistence | 77.496 s |
| Persistence share of ingestion | 47.19% |
| Original document ready after experiment timer start | 180.148 s |
| All 33 documents verified ready | 214.527 s |
| All 33 documents total | 873,292 bytes, 973 chunks |

The timer starts before queue initialization/login, and all 33 uploads are sent
before the worker runs. Therefore the ready figure includes that preparation and
queue sequencing; it is not an isolated HTTP upload-to-ready production percentile.
The acknowledgement at 4.408 seconds is cumulative from that timer, not the duration
of the upload request. The scoped controls add work after the main document. The
938 versus earlier 939 chunks reflects the changed document boundaries when the
same text is ingested as one file; do not infer a retrieval-quality comparison from
those counts.

The historical fourteen-file run reached ready in 199.385 seconds for its own
layout. This is one shared-laptop observation with a different upload layout and
32 added control documents, so no percentage speedup against that run is claimed.
The verified improvement is that the original single-file persistence failure is
resolved. Persistence still consumes 77.50 seconds; investigate the existing SQL
and vector-index work under the application role before increasing concurrency.
The remaining 86.73 seconds combine embedding, parsing, chunking and other stages;
the present measurement does not separate those costs.

This validates a 650-context, 938-vector stress case of the identified failure.
It does not establish throughput or memory safety for every large PDF, OCR document
or file at the installation's maximum upload size.

## Models, execution identity and resource limits

- Embeddings: BGE-M3 revision `5617a9f61b028005a4858fdac845db406aefb181`, TEI 1.9.4,
  GPU float16, batch token limit 1024, client batch items 2, CLS pooling.
- Reranker: BGE-reranker-v2-m3 revision `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`,
  TEI 1.9.4 GPU float16. The read-only mounted weights were checked against actual
  SHA-256 `d9e3e081faff1eefb84019509b2f5558fd74c1a05a2c7db22f74174fcedb5286`.
  Server limits are 2048 tokens and four client items; the application scorer uses
  the existing smaller 1024-token/two-item profile. Automatic truncation remains enabled.
- New generator and independent NLI runs: none. Their pinned earlier models and
  completed outcomes are in [the cited-answer report](spanish-e2e-results-2026-10-03.md).

All 128 positive queries produced actual 32-candidate captures. The 32 controls
produced one to three candidates each. Positive 32-candidate scoring median is
2.4632 seconds and nearest-rank p95 is 3.0169 seconds. Across all 160 queries,
including the smaller control pools, median is 2.3589 seconds and total scoring
time is 325.343 seconds. These are serial scoring times on a shared laptop,
not comparable to the earlier eight-passage 272 ms GPU pilot without qualification.

Actual archived capture head: `9eabdbf8e51c5fe4e57673e89a742fe6be6938ab`.
Capture tree: `4f20a385fe98654b78410b4a8c64c861a7319007`.
Runner image: `sha256:906ce21d27968f6b2ec1d5d83601bec84f875d74bef5cbfaf8eafee948458d88`.
The opt-in pipeline test passed: **1 passed in 409.04 seconds**, wrapper 432.686
seconds, exit 0. Its archive/log hashes and the complete capture/score identities
are exported in the JSON. Subsequent source edits resolve fixture type annotations
and export documentation; they do not rerun or replace the frozen measurement.

On the RTX 5070 Ti Laptop GPU (12,227 MiB), sampled aggregate VRAM peaks were
5,644 MiB in embedding and 5,508 MiB in reranking. Minimum free host RAM was
3,380.86 MiB and 3,852.95 MiB respectively. Neither resource monitor aborted.
GPU utilization peaked at 78% and 98%; aggregate GPU observations include other
host activity and are not per-model attribution. Models were run sequentially.

Earlier attempts are retained: Docker engine unavailable before capture; two
coordinator readiness callback incompatibilities before uploads; missing test-tenant
fixtures corrected before successful qualification; a Docker engine outage during
an ingestion rerun; and the separate full local suite timeouts. They are failures,
not observations averaged into successful timings. See [delivery record](upstream-acceptance-2026-10-03.md).

After the last scoring operation, the user's requested `docker desktop stop` and
`wsl --shutdown` both completed with exit 0. No further Docker run is needed for
this delivery. The isolated benchmark volume is preserved for audit/resumption;
raw documents, candidate text, vectors and full logs remain ignored, outside Git.

## Continuation decisions

1. Obtain Martin's review of independently green upstream #16 and #17. Keep all
   fifteen older PRs open. The ingestion and gate changes remain separate fork
   drafts with their own green workflows; none has been merged or promoted upstream.
2. Treat the corrected local gate as the next comparator. Freeze a paired Spanish
   generated-answer/citation experiment including the impossible controls, compare
   corrected BGE with optional Jev, and retain independently published references
   plus a separate automatic claim-support judge. Reuse the completed retrieval
   capture; do not call admission success generated-answer accuracy.
3. Measure claim-support and abstention on the 31 admitted impossible controls,
   and measure persistence statement/index costs with repeated same-file runs.
   Require an improvement without new private-data export or weaker RLS before
   proposing another production optimization.
4. The fork now accepts an optional authorized-private-corpus Jev mode as a product
   tradeoff; see [private-corpus decision](jev-private-corpus-decision-2026-10-03.md).
   Deployment-specific processor authorization, retention agreement, finite budgets
   and verified single external dispatcher are needed before an installation sends
   private content. The completed public studies do not constitute that activation.
