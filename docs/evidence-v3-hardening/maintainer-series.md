# Local maintainer review series

The original integration history and branches remain preserved. A future review should use the current upstream baseline recorded in [current state](current-state.md), refetch before submission, and test each actual merge result. No push, PR, fork-main move, or deploy is authorized by this phase.

1. `fix/evidence-v3-series-portability-v9` (`cc92f01`) places architecture detection, bounded diagnostics, migration test harness, Windows selector bootstrap, Windows licence/frontend gates, and LF shell attributes before PR 01.
2. PR 01–04 are `b65fc47`, `1f0dd1f`, `273df29`, and `e050c30`. The proxy prerequisite `4a9e9cd` precedes PR 05 `6425c01`; neutral evaluation helpers are `1dd18c3`.
3. PR 06 `c1d5424` includes its own import-order correction. PR 07 `ddb6fc5` carries the binary rubric contract at its consumer. PR 08 is `e253f30`; integrated security is `0a94ed4`; release reporting is `b7302eb`.
4. Core hardening ends at `7e446fd` in `fix/evidence-v3-series-hardening-v9`, tree `93a088dbf604811b938e5e73b18566937d200626`. The report branch is a docs-only descendant and is identified separately in [the manifest](publication-manifest.json).
5. Optional R1 is preserved separately at `fix/evidence-v3-series-r1` (`0d0844b`) on an earlier neutral base; it is research, not an ancestor of this core integration. The one-file independent frontend security branch `c11755806dd4b6bd159bee37d8c7aae49f7f5d5f` also remains distinct. Defaults remain off.

These local boundaries are materialized, with exact-tip results in [per-PR validation](per-pr-validation.md). Earlier full integration results do not qualify new tips by themselves. Before any remote step, refresh the remote baseline, test actual merge refs, audit history for credentials/private corpora, and finish applicable exact-candidate browser acceptance. No remote action is authorized in this pass.
