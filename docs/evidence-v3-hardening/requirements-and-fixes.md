# Requirements and repairs

The locally supplied handoff's `01_REMEDIATION_PLAN.md` and `02_EVALUATION_AND_EXIT_GATES.md` define the qualification scope. The handoff is intentionally outside the tracked publication. This table separates implemented changes from evidence still needed.

| Requirement | Change or evidence | State |
| --- | --- | --- |
| BR-01 proxy guard | Static parser recognizes literal and approved `apiTarget` declarations; rejects absent, malformed, misdirected, and comment-only routes. | implemented; local tests |
| BR-02 neutral harness | `eval.evidence_common`, `qasper_common`, and `contract_nli_common` hold shared scoring/annotation logic; packet runners no longer import R1 trial modules. | implemented; boundary test |
| BR-03 old ledgers | Frozen 176 and descriptive 416 outcomes rescored byte-identically in ignored local output, without provider calls. | passed offline |
| SC-01–06 Score | Public/synthetic-only opt-in, bounded pre-parser body recorder and typed diagnostic failures. One newly observed mass violation; no validator relaxation. | engineering implemented; model contract unresolved |
| ST-01–06 strict support | Failure layers exposed, equivalent decimal strings normalized, final-source fail-closed preserved. | deterministic repair; semantic calibration open |
| RP-01–04 R1/packets | Historical paired human-label comparisons and alternate index retained. A frozen public Spanish/English transfer reindexed structural chunks at equal token budgets; all 24 test questions reached a top-1 ceiling, with no packet gain. Optional flags remain off. | experimental isolated; quality gain unproven |
| OP-05–08 Jev | Per-call reservations, bounded two-wide windows, global deadline, one retry for known 429/529, whole-order TEI fallback with visible degraded metadata. | local tests; load qualification open |
| OP-01–04 shared quota | Existing single-worker restriction retained; no shared coordinator enabled. | not implemented for multiworker |
| UI-01–04 | Exact final v10 authenticated browser passed 11 default, 10 experimental, and 12 concurrent local searches with real auth/RLS/TEI. One separately approved synthetic-source run joined real local generation, Jev ranking, strict support, RLS and a bound citation; the browser and combined lanes have not been joined. | separate narrow passes; exact v10 browser passed |
| CI-01–03 | Exact final v10 Linux `make check` passed 1,004 backend/15 skips and 450 frontend; the exact final Windows browser passed. Full `npm audit` at the final lockfile found zero advisories, including development dependencies. V10 foundation and PR01/PR06/PR07 Windows gates passed with production audit zero advisories. Other intermediate and final Windows gates continue. | partial exact v10 series; final Windows pending |
| PUB-01–03 | Local manifest and review plan; historical refs preserved. | no remote publication authorized |

No default Jev, R1, packet, counterevidence, or strict-support setting was enabled. A model or experimental component may remain in the codebase without being qualified for default use.
