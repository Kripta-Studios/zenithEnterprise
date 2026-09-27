# Requirements and repairs

The locally supplied handoff's `01_REMEDIATION_PLAN.md` and `02_EVALUATION_AND_EXIT_GATES.md` define the qualification scope. The handoff is intentionally outside the tracked publication. This table separates implemented changes from evidence still needed.

| Requirement | Change or evidence | State |
| --- | --- | --- |
| BR-01 proxy guard | Static parser recognizes literal and approved `apiTarget` declarations; rejects absent, malformed, misdirected, and comment-only routes. | implemented; local tests |
| BR-02 neutral harness | `eval.evidence_common`, `qasper_common`, and `contract_nli_common` hold shared scoring/annotation logic; packet runners no longer import R1 trial modules. | implemented; boundary test |
| BR-03 old ledgers | Frozen 176 and descriptive 416 outcomes rescored byte-identically in ignored local output, without provider calls. | passed offline |
| SC-01–06 Score | Public/synthetic-only opt-in, bounded pre-parser body recorder and typed diagnostic failures. One newly observed mass violation; no validator relaxation. | engineering implemented; model contract unresolved |
| ST-01–06 strict support | Failure layers exposed, equivalent decimal strings normalized, final-source fail-closed preserved. | deterministic repair; semantic calibration open |
| RP-01–04 R1/packets | Historical paired human-label comparisons and alternate index retained, optional flags off. | experimental isolated |
| OP-05–08 Jev | Per-call reservations, bounded two-wide windows, global deadline, one retry for known 429/529, whole-order TEI fallback with visible degraded metadata. | local tests; load qualification open |
| OP-01–04 shared quota | Existing single-worker restriction retained; no shared coordinator enabled. | not implemented for multiworker |
| UI-01–04 | Historical and fresh exact-candidate authenticated browser evidence passed (11 default, 10 experimental, 12 concurrent local searches); combined real generator/Jev/support lane still required. | scripted-generation browser pass; combined live lane open |
| CI-01–03 | Exact core candidate Windows `make check` passed; Linux backend Ruff/format/Pyright and 1,004/14 application-role tests passed; Linux frontend clean install/types/450 tests/build/audit passed. | local Windows/Linux engineering pass |
| PUB-01–03 | Local manifest and review plan; historical refs preserved. | no remote publication authorized |

No default Jev, R1, packet, counterevidence, or strict-support setting was enabled. A model or experimental component may remain in the codebase without being qualified for default use.
