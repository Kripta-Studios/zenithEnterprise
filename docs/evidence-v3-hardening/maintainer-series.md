# Local maintainer review series

The original integration history and branches remain preserved. A future review should use the current upstream baseline recorded in [current state](current-state.md), refetch before submission, and test each actual merge result. No push, PR, fork-main move, or deploy is authorized by this phase.

1. Historical PR 01–04 preserve their original changes.
2. The local `fix/evidence-v3-series-prerequisite` head `f0b8115` carries one proxy parser/backport after PR 04 and before PR 05, expanded guard regression, and Windows portability. `fix/evidence-v3-series-pr05` is `87e4981`.
3. `fix/evidence-v3-series-common` at `a9f7f39` carries neutral evaluation scoring before packets. Optional R1 is retained separately at `fix/evidence-v3-series-r1` (`0d0844b`); core PR 06 has no R1 import.
4. Core PR 06 is `636d474`; PR 07 is `772afa2`, with the binary rubric contract placed at that earliest consumer; PR 08 is `6b0a090`. Integrated security is `06d8ca5`, and release reports end at `b6a9305`. The one-file independent frontend security branch `c11755806dd4b6bd159bee37d8c7aae49f7f5d5f` remains distinct from this integrated lockfile change.
5. Hardening repairs end at `4092f27` in `fix/evidence-v3-series-hardening-v3`. This is the exact local code candidate in [the manifest](publication-manifest.json). It omits optional R1 runtime/index changes while preserving the R1 research branch and reports. Defaults remain off.

These local boundaries are materialized, but intermediate tips have only the evidence in [per-PR validation](per-pr-validation.md). The historical full green integration result cannot be inherited by a recomposed branch. Before any remote step, refresh the remote baseline, run applicable full checks on actual merge refs, audit history for credentials/private corpora, and rerun authenticated browser acceptance at the exact executable candidate. No remote action is authorized in this pass.
