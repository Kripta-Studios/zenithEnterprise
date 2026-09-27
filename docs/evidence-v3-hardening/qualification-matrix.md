# Component qualification matrix

`passed` here means the stated narrow test passed. It does not imply deployment qualification. Quality and operational promotion require the handoff's G3/G4 gates and approved criteria.

| Component | Engineering | Quality evidence | Operations | Default/recommendation |
| --- | --- | --- | --- | --- |
| Legacy/default TEI path | exact core candidate authenticated Windows browser passed 11 checks; experimental UI passed 10 with scripted generator; backend and frontend engineering gates passed on Windows and Linux | baseline retained | 12 local concurrent requests passed with no degradation | preserve existing default |
| Jev Noul reranking | bounded adapter/concurrency/retry tests | historical human-label QASPER 93/147 complete versus TEI 75/147; new synthetic 10-language architecture probe tied TEI wherever valid, with two bundled failures | tiny two-wide latency probe, no sustained load | `experimental_isolated`, off |
| Jev Score | strict parser and diagnostic capture | old 8/40 batch failures; new 47/48 valid, one 0.99 mass | typed failure and complete fallback | `experimental_isolated`, off |
| Strict support | source fail-closed and failure-layer repair | SciFact oracle and synthetic development checks; no independently labeled generated-answer qualification | outage blocks unchecked release | `experimental_isolated`, off |
| R1 structural grouping/index | neutral harness separated; original alternate index retained | QASPER mixed/negative, ContractNLI positive complete-evidence but top-1 loss | active index migration not tested | `experimental_isolated`, off |
| Packets/counterevidence | source-preserving optional selector | QASPER TEI one loss; otherwise null complete-evidence effect | full answer path not qualified | `experimental_isolated`, off |
| Proxy prerequisite | focused positive/negative guard fixtures | security compatibility, not model quality | normal local routes | include once before dependent UI slice |
| Single-worker Jev quota | local reservation and guard tests | not applicable | supported only under declared single-worker scope; restart accounting not durable | do not claim multiworker |
| Multiworker Jev | no shared coordinator | not applicable | `not_run`/unsupported | `not_deployed` |
| Full live inference E2E | historical browser used scripted generator; separate new real Jev pilot | no combined real generator, support, Spanish-domain gold | no production load | `not_run`, no promotion claim |

The evaluation history is retained even where optional mechanisms have null or negative effects. No default or external-purpose processing flag changed in this pass.
