# Local publication slice validation

The branches below are local review candidates. No PR or remote CI exists. `focused` means only the cited tests ran on that branch; it does not inherit a full gate from a descendant. The final integration gate is recorded separately in the publication manifest.

| Slice | Exact local head | Validation at that head | State |
| --- | --- | --- | --- |
| PR 01 judge protocol | `b354b8ee29af99975bd5308d2197a9f002c512cb` | Historical feature validation only | `historical_only` |
| PR 02 optional Jev | `e5f37c2c970e5c380998478548dd78a78a05a988` | Historical validation only | `historical_only` |
| PR 03 hybrid | `bab1578782aa26dad858ef7d258407f749e85d08` | Historical validation only | `historical_only` |
| PR 04 direct scope | `92e42bde2ac5522950242ae06ed3834b46f5497a` | Historical validation only | `historical_only` |
| Proxy and portability prerequisite | `f0b81150e67048c7973e0e25582c08e808a8dd52` | Historical proxy tests, expanded regression checked on final code | `focused_only` |
| PR 05 coverage/UI | `87e4981770dd6e1245bb0503a9b90e29ff8a1959` | Historical simulated merge three proxy tests and Linux-target Pyright; no new full gate | `focused_only` |
| Neutral evaluation prerequisite | `a9f7f39934ed13fe2fe469ebb27e3d9d5cc4e10f` | Neutral import regression and byte-identical offline rescoring of seen QASPER ledgers | `focused_only` |
| Optional R1 research | `0d0844ba236a08d4983bfc93cb98b76ab0497406` | Historical public mechanism trials; separate from core ancestry | `research_only` |
| PR 06 packets | `636d474be4caa20e0c35703ffedeb403ea0f853b` | Four packet/neutral tests passed; one import-order lint issue repaired on final hardening slice | `focused_only` |
| PR 07 strict support | `772afa2f405d930b3f63c95c2818d43df8f6cecf` | Rubric contract moved here to remove R1 dependency; predecessor 40 focused tests passed, exact v3 tip full gate pending | `focused_only` |
| PR 08 qualification/UI | `6b0a090ec881eb8cf96061ab135ba318de368bbc` | Four neutral QASPER tests passed on predecessor; 38 Jev/hybrid/packet tests passed on the later hardening integration | `focused_only` |
| Integrated security | `06d8ca55ac85fd49621852b0626ee78d1515ab6d` | Lockfile patched, clean install and audit on final descendant; independent one-file security branch remains distinct | `focused_only` |
| Release validation/report | `b6a9305d3df7ad6eec451a08d2bc1fa0ed7b6653` | Historical authenticated browser 11 default + 10 experimental and 12 local concurrent searches at original release code `1862072`; not rerun at this tip | `historical_only` |
| Hardening integration | `4092f2735d30e7bc360bce88113c246eaf1fda60` | Windows `make check` exit 0 on exact tree `d69c37070fe22d0069804abea5708c835add8317`: Ruff, format, Pyright, 1,004 backend passed/14 skipped, licence check, frontend types and 450 tests in 43 files. Linux archived same tree: Ruff, format, Pyright, 1,004 backend passed/14 skipped on application-role PostgreSQL; clean frontend install/types/450 tests/build/production audit passed. Windows fresh authenticated browser 11 default + 10 experimental, plus 12 local concurrent searches passed; experimental generator scripted and Jev off. | `local_engineering_pass` |

The exact Windows gate log is ignored locally as `.scratch/evidence-v3-hardening/series-v3-make-check-2.log`, SHA-256 `a57c7137dc2a00b14ef2a46f3f5c1c11ccba09b68e7f5f249ee63be07c1f1154`. The Linux backend test log SHA-256 is `445b283edb1c7581d38fed54872026056bd0d3d07028b22611cae7118a32fc9d`; Linux Ruff and Pyright pass logs are `e51bc9533d7e803c6f23f71a753604f119e2ad8584bcaed1f30d6ebf8d765b92` and `48b2ece9985aa0d5ce31fcc374bdc5f0d2a61aa71c76b3d9423d63911eeedcad`. An earlier development-branch full run failed one concurrency expectation; the corrected regression passed, and this recomposed exact-tip run passed. The original release code `1862072e55f3d79877334964b0e1b3a8f473a39f` and report `5cd3f9ca917a5e14a2db8d448e712c9d45d69606` remain preserved. The hardening development branch `fix/evidence-v3-hardening` includes optional R1; the review integration branch above omits R1 code from core ancestry while retaining its local branch and reports. No intermediate slice is marked fully qualified without an actual applicable gate on that exact tip.
