# Decision: offer Jev reranking for authorized private corpora

**Evidence update:** the [completed corrected-BGE repeat](corrected-bge-e2e-results-2026-10-03.md)
produces BGE 34/128 versus Jev 31/128 strict successes. Jev's paired difference is
-2.34375 points, 95% interval [-9.02256, +3.96825]; neither improvement criterion passes.
The original positive comparison below is historical and no longer supports a quality
advantage against the corrected local baseline. The user's optional adoption direction
remains recorded, but retain BGE as default and do not justify private-data export using
the old gain. Any optional deployment remains a corpus-owner product decision under the
existing processing/topology boundaries, not a demonstrated superiority result.

Status: approved product direction for this fork by the user's 2026-10-03 instruction.
This supersedes the previous recommendation against a private-corpus pilot. It records
an adoption decision and its implementation boundary; it does not assert that a private
deployment has been enabled or that Martin has approved this optional contribution.

## Original adoption rationale (historical comparator, now superseded)

The completed Spanish generated-answer experiment replaces the small saturated pilot
with 128 published-reference questions and mandatory citation checks, followed by a
different local multilingual entailment judge. The strict primary outcome improves
from 10/128 to 20/128. The absolute gain is 7.8125 percentage points, with paired
article-bootstrap 95% interval [1.5504, 14.7287]. The preregistered meaningful-gain
criterion passes. Jev contributes thirteen exclusive primary successes and loses three,
for ten additional successful outcomes on the same 128 questions.

The improvement is useful at the actual system boundary: an otherwise unanswered
question can obtain a referenced, independently supported answer. Jev delivers 74
answers versus 42 with the measured local configuration. The small recovery cost is
also encouraging: 274 new public scoring calls cost about $0.007438 in recorded input
tokens. That observation supports an explicitly budgeted option where the corpus owner
accepts external processing. It does not predict a production invoice or prove lower
whole-query latency.

The decision does not require pretending that the strongest preregistered criterion
passed: its lower bound is below two percentage points. Nor does it require relabelling
all delivered answers as correct: only twenty Jev outcomes meet the primary proxy.
Eleven of the thirteen exclusive successes coincide with the legacy lexical gate
stopping BGE before generation. This is an important reason to validate a corrected
local comparator; it does not erase the benefit observed in the configuration actually
tested. The newly authorized product tradeoff is to offer the observed improvement
while completing that comparison, rather than make optional adoption depend on a
claim of universal or intrinsic provider superiority.

Reference: [complete measured results and limits](spanish-e2e-results-2026-10-03.md),
[aggregate JSON](spanish-e2e-results-2026-10-03.json), and
[paired case diagnostics](spanish-e2e-cases-2026-10-03.csv).

## What private-document activation means

Private documents can use an external processor when their owner authorizes that
processing. Keep document storage, embeddings, vector search, user access, answer
generation and citation binding local. Jev receives the question and the bounded
rendered source passages needed for reranking. Both can be confidential. Sending
those passages is still disclosure to a third-party processor; limiting the payload
reduces its extent but does not make the processing on-premises.

Use the existing purpose flags, authorization callback, source identity checks,
bounded requests and visible local fallback in the integrated fork. Enable reranking
for the approved corpus only. Segmentation and external claim support are separate
purposes and remain disabled unless separately selected. RLS must restrict the source
pool before dispatch, and the callback must revalidate the current source identity
and access. Read permission and permission to send content outside the installation
are distinct decisions; a global API key supplies neither.

Do not copy private contents into benchmark fixtures, Git evidence or request-body
logs. Keep audit records useful through provider/model, purpose, decision, source
identifiers, token/call accounting and outcome, rather than raw confidential payloads.
Requests denied by the corpus's external-processing policy must remain local.

## Provider statements and account-specific conditions

TypeSafe states that it does not train models on customer inputs. Its published
privacy policy nevertheless allows retention and processing in the United States.
The documentation offers zero data retention for enterprise customers; it does not
establish that the current API account has that arrangement. Verify the account's
actual retention and processing agreement before describing it as ZDR or region-bound.
[Privacy policy](https://typesafe.ai/legal/privacy-policy),
[legal documentation](https://docs.typesafe.ai/legal).

The published DPA describes processing on the customer's behalf and international
transfer terms. Account-specific contractual coverage, customer restrictions and
the intended categories of documents remain deployment facts to verify. Benchmark
accuracy cannot establish them.
[Data Processing Agreement](https://typesafe.ai/legal/data-processing).

The price checked on 2026-10-03 is $0.042 per million input tokens for pinned
`jev-1.13.0`; output tokens are free. Budget limits must include earlier consumption,
unknown outcomes and rejected/retried requests, rather than treat the low observed
recovery cost as permission for an unlimited service.
[Official model reference](https://docs.typesafe.ai/models).

## A workable initial topology

The existing quota, concurrency limiter and breaker are process-local. Use one
verified API process as the sole external dispatcher. Keep Jev credentials and
external-purpose flags out of the ingestion worker; its embedding/classification
path stays local. Route MCP consumers through that API rather than construct
additional external judge instances in separate clients. These constraints allow
a bounded pilot without building the distributed quota system excluded from scope.

`JEV_SINGLE_WORKER_ACK` is an acknowledgement to accompany verified topology,
not proof that the topology is safe. Check effective API worker count, dispatch
paths and worker environment. Apply finite request/token/concurrency budgets and
stop on budget exhaustion or unknown provider outcomes. A process restart must
not silently grant a new approved paid allowance. Retain durable accounting for
the session and reconcile it before any restart with external dispatch enabled.

Keep the pinned local reranker available for denied export, provider failure,
deadline expiry and quota exhaustion. Report fallback/degradation through the
existing contract. Reranking does not relax the mandatory-citation rule; the
generator still has to abstain when it cannot bind evidence.

## Delivery and evidence boundary

The two contributions Martin requested remain entirely independent of this
decision: [judge PR #16](https://github.com/Martinhdeez/zenithEnterprise/pull/16)
and [proxy PR #17](https://github.com/Martinhdeez/zenithEnterprise/pull/17).
Both have actual green upstream backend/frontend Actions and are ready for review.
Their original branches and the fifteen older PRs were not rewritten, merged or
closed. Upstream may keep its current local-only direction even while this fork
offers an optional externally processed mode.

This delivery changes the documented product decision and validates the next
local improvements. It does not switch an unspecified customer installation's
flags, transmit any private document, claim an executed private-corpus benchmark,
or install a distributed external quota coordinator. No private corpus, concrete
customer processing agreement or target deployment was supplied for an activation.
The existing integrated fork's optional provider path remains the implementation
starting point; the accepted standalone PRs do not import it.

## Corrected local comparator: subsequent measured result

The separate [fresh gate validation](local-gate-and-ingestion-results-2026-10-03.md)
now completes: 128 previously unused article families, plus 32 published impossible
controls, with actual local embeddings and reranking. Correct-evidence admission
increases from 32/128 to 113/128 under the corrected local gate. It meets its frozen
admission criterion, while both gates still admit 31/32 impossible controls.

This supports fixing the local comparator before drawing a new provider superiority
claim. The fork's approved optional adoption decision remains a product tradeoff,
but the old 10-versus-20 generated-answer result must not be presented as measured
against this corrected local baseline. No new generation, Jev calls or private data
processing occurred in that gate validation. The subsequent generated-answer repeat
is now complete: [corrected BGE results](corrected-bge-e2e-results-2026-10-03.md),
34/128 BGE versus 31/128 Jev, with neither Jev improvement threshold met.
