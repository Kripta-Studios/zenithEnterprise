# Corrected baseline, ingestion and MCP: continuation decisions

## What is established

The corrected Spanish cited-answer comparison is complete: BGE **34/128** versus
Jev **31/128**, paired difference **-2.34375 points**, article bootstrap 95% interval
**[-9.02256, +3.96825]**. Neither preregistered Jev improvement criterion passes.
The old 10-versus-20 comparison is historical evidence against a flawed local gate,
not a current reason to activate external processing of private documents. The
optional private-corpus direction remains recorded; this experiment does not establish
its quality justification, privacy acceptance or multi-process deployment safety.

Atomic persistence is **4.14x faster** in the paired local measurement. One fresh
844643-byte, 938-chunk upload reaches observed ready in **136.013 seconds** with real
GPU embeddings. MCP now exposes nine bounded tools, a capabilities resource and a
cited-answer prompt. Reading eight sources together is **6.89x faster** in the SDK/DB
measurement, with **87.5% fewer SQL operations** and fresh authority.

Read the complete [quality report](corrected-bge-e2e-results-2026-10-03.md),
[persistence/upload report](persistence-upload-results-2026-10-03.md), and
[MCP workflow and acceptance limits](mcp-agent-workflow-2026-10-03.md).

## Martin's acceptance requirements

Keep the independent provider-neutral judge and Vite proxy guard upstream PRs
[#16](https://github.com/Martinhdeez/zenithEnterprise/pull/16) and
[#17](https://github.com/Martinhdeez/zenithEnterprise/pull/17) independent and unchanged.
Their earlier upstream CI is green; review and adoption remain Martin's decision.
The other fifteen upstream PRs remain open; do not describe all seventeen as CI-green.
No new work here changes those branches or closes any upstream PR.

This comparison now exercises Spanish generated answers, mandatory citation binding
and real audit persistence. Published human reference spans and a separate automatic
multilingual entailment model replace implementer relevance guesses. They do not equal
external human adjudication of generated claims. The same already observed cohort was
reused for corrective analysis, so the request for a harder untouched end-to-end set
remains open. Ranking/source hit gains alone still do not meet his product criterion.

Local processing remains the default. GPU TEI and upload/persistence improvements
advance his practical direction without depending on Jev. The local MCP transport and
existing Keycloak intranet transport retain their current user/tenant/label boundaries.

## Next experiments, in order

1. **Generated claim support.** Diagnose the 42 BGE and 49 Jev outcomes that contain
   a grounded reference yet fail strict NLI. Separate unsupported additions, uncited
   sentences, valid paraphrases, source-window limitations and evaluator disagreement.
   Compare concise Spanish cited-answer prompts and local generators on development
   data. Freeze prompt/model/judge and thresholds before a new article-disjoint public
   Spanish holdout with negative controls. Report quality, answerability, citation
   identity, entailment, inference latency and cost independently. Automatic judging
   remains explicitly automatic; obtain external adjudication if Martin requires it.
   Do not retune thresholds or select questions to manufacture a provider win.

2. **Remaining ingestion time.** The subsequent
   [paired GPU ingestion experiment](ingestion-phase-results-2026-10-03.md) identifies
   embeddings as the dominant component of the historical 93.349-second observation.
   The optional bounded `gpu-local` recipe reduces measured non-persistence medians
   from 63.383 to 29.863 seconds and observed ready from 93.420 to 59.270 seconds.
   These are three new paired uploads per arm, not a controlled comparison to the
   earlier 136-second upload. Embedding and persistence now take about 29 and 27
   seconds respectively. Profile vector serialization, INSERT/index work and commit
   in this new workload; the old 10.393-second vector INSERT is historical evidence.
   Keep full-vector storage and one atomic replacement transaction.
   Compare fresh upload pairs at fixed layouts/sizes and include dedup hits, retry,
   cancellation, RLS and failed-job behavior. Accept further tuning only with lower
   ready p50/p95 and no isolation, rollback or content loss regression.

3. **Agent transport/load acceptance.** Run the same multi-source workflow over actual
   stdio and authenticated intranet HTTP with the selected local client/model. Measure
   queue, authorization, database and inference time under one/two concurrent agents.
   Check revocation during waiting and generation, final citation reauthorization,
   bounded cancellation, hidden-ID equivalence and prompt-injection handling. The
   current 0.513-second batch result is in-process SDK plus DB, not a network SLA.

4. **Upstream review.** Provide Martin the independent existing PRs and their exact
   green check links. Offer the local persistence/MCP changes as separate reviewable
   slices only after he requests them. Do not publish a new upstream series or combine
   them with the Jev adoption proposal. Fork publication and its CI are separate from
   his upstream acceptance.

## Actual local validation and remaining delivery gate

Completed: corrected paired e2e integration **1 passed**, independent grading of all
128 pairs; final atomic ingestion **22 passed**; MCP functional **54 passed / 3 optional
skips**; persistence, fresh upload and MCP benchmarks **one passed each**. Full strict
types pass with the complete host environment. Backend lint/format and license checks
pass. Exact-lockfile frontend tests pass **450 tests / 43 files** using Vitest 4.1.11
threads on Windows; frontend types and production build pass.

The local complete backend suite did **not** finish: its 1800-second runner budget
expired around 58%, without assertion failures observed before timeout. Thin-runner
types also failed because Node lacked libatomic and a retry lacked Torch; those are
retained failures, not passes. The complete host types check resolves the type check,
but does not complete the full backend test suite. Therefore local `make check` is
not claimed green. The full locked-dependency GitHub backend/frontend jobs must pass
on the published fork candidate before incorporating it into fork main. Docker/WSL
remain stopped as requested; GitHub completes that delivery gate.

No new paid provider calls, new database, schema migration or framework were added.
Raw sources/completions, local credentials and model caches remain outside Git.
