# Zenith v3 hardening: current state

This pass starts from local release report `5cd3f9ca917a5e14a2db8d448e712c9d45d69606`, whose executable release code is `1862072e55f3d79877334964b0e1b3a8f473a39f`. Historical integration `0a24cc34b05a1b055452069849ebea61a4d9aba6` and all feature branches remain intact. At the baseline read-only check, `main`, `origin/main`, and `upstream/main` pointed to `33b48812c95150348c52d2519159780252c92db2`. This pass works on local `fix/evidence-v3-hardening`; no remote ref was written.

The historical authenticated acceptance covered real login, application-role PostgreSQL/RLS, source ingest and original download, text/PDF highlights, tenant and label checks. The same local lanes were rerun at exact R1-free candidate `4092f2735d30e7bc360bce88113c246eaf1fda60`: 11 default and 10 experimental checks passed, with 12 concurrent local searches all HTTP 200 and no degradation. The experimental generator boundary was scripted and Jev was off in both rounds. See [release validation](../evidence-v3/release-validation-2026-09-27.md) and [current matrix](live-e2e-matrix.md). Historical and new evidence indexes are ignored locally and tied to their respective SHAs.

QASPER consists of real papers and human evidence labels. The old 240-paper and later disjoint 176-paper cohorts have both been inspected. The later 147 addressable cases favored Jev Noul over TEI for complete evidence, 93 versus 75 (+12.2 points, paper-bootstrap 95% interval +6.1 to +18.4). The descriptive 416-paper combination is not a new locked test. The old ledgers remain frozen. See [QASPER extension](../../backend/eval/reports/evidence-v3-qasper-extension-2026-09-27.md).

## Workstream state

| Workstream | Current disposition |
| --- | --- |
| Proxy guard and neutral evaluation helpers | Code repaired and placed in local prerequisite slices before dependent PRs; intermediate full checks remain pending. |
| Score | Raw public diagnostic captured one new 0.99-mass response; strict typed failure retained. Old payloads remain unavailable. |
| Strict support | Deterministic numeric equivalence and failure-layer trace repaired; generated-answer calibration remains unqualified. |
| R1 and packets | Existing human-label results preserved; no new representative locked experiment in this pass. Optional, default off. |
| Jev operations | Bounded concurrency and one known-rate/overload retry added; single-worker guard retained. Sustained capacity and distributed coordination unqualified. |
| Frontend tooling | Vitest 4 targeted upgrade and two-worker test setting; final build/audit/browser gates recorded separately. |
| Publication | Local review series materialized through `4092f2735d30e7bc360bce88113c246eaf1fda60`, with R1 separate. No push, PR, fork-main advancement, default change, or deployment. |

## Dependency sketch

`upstream main -> historical PR 01-04 -> one proxy/portability prerequisite -> PR 05 -> neutral evaluation helpers -> PR 06-08 -> security/release validation -> hardening`. Optional R1 branches from the neutral prerequisite and is preserved separately. The graph is materialized locally; this does not assert that each proposed merge ref passed a full gate. Runtime code does not import `backend/eval`; packet evaluation obtains shared scoring from neutral modules rather than R1 trial modules.

## Local validation commands

From the repository root on Windows, use `PYTHONUTF8=1` and the existing `scripts/windows_selector_bootstrap` Python path for real PostgreSQL tests, with a disposable `ZENITH_JWT_SECRET`. Run `make check` for backend/frontend/static/license gates, `npm ci` in `frontend`, then `npm run build` and `npm audit`. The final exact test results and conditional skips are recorded in [per-PR validation](per-pr-validation.md) and [conditional tests](conditional-tests.md).
