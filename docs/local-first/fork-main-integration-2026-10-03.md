# Fork main consolidation

The user authorized merging the published fork work into `Kripta-Studios/zenithEnterprise`
main and retiring incorporated branches on 2026-10-03. The integration starts at
`f6dd7aee70611aeb6d08658b2c4164f9fd8effbf`, which already contains the v10 series.
No upstream adoption or private-customer activation follows from this fork merge.

## Incorporated work and provenance

| Published source | Original head | Delivery |
| --- | --- | --- |
| `feat/mcp-intranet-auth` | `f344b008fa95` | Local stdio MCP, authenticated intranet transport, Keycloak audience/session boundary, existing ingestion upload adapter; includes `feat/local-mcp-stdio` |
| `fix/deterministic-test-timing` | `9b5a84fee44b` | Stable filesystem/upload timing and bounded frontend worker pool |
| `fix/embedding-final-backoff` | `595bbe2e3175` | Avoid sleeping after the final failed embedding attempt |
| `fix/large-document-embedding-inserts` | `021ebefe4690` | Bounded vector INSERT groups within atomic document replacement |
| `fix/relevance-before-rerank-gate` | `d8eb50e6f3b4` | Read lexical evidence from authorized candidates before local reranking |
| `perf/local-relevance-new-questions` | `9beaf881a65f` | Public Spanish studies, local GPU override, single-file measurement and private-corpus decision; includes the baseline and complete cited-answer research branches |
| `fix/evidence-v3-series-report-v10` | `7c4af947617d` | Final v10 submission inventory and evidence reconciliation |
| `feat/local-judge-contract-standalone` | `36f4f7d7155d` | Reconcile independent upstream provenance with the richer contract already in main |
| `fix/vite-proxy-prefix-guard-standalone` | `9e9bd377dbda` | Add extraction regression controls while retaining the richer fork parser |

The v10 provider-neutral contract already carries score kinds, model identity,
source fingerprints, complete/partial states, duplicate-text handling, deadlines
and external-processing policy. Replacing it with the minimal upstream extraction
would remove those features. Its fork implementation and tests are retained, while
the standalone branch remains unchanged for upstream PR #16.

The relevance merge preserves provider-aware `NOT_ASSESSED`, source-change refusal
and direct-mode behavior. Only the local classification path takes lexical share
from the pre-rerank pool. The Vite resolution preserves configurable API targets,
the isolated optimizer cache, target-safety checks and the missing-prefix/unrelated-
fetch controls; the test worker pool now has explicit minimum and maximum values.

The public capture wrapper returns the richer fork's assessment metadata along with
hits and degradation. Historical results remain bound to their original measured
source heads; integrating their harness is not a new generated-answer or GPU run.
Duplicate in-progress notes are removed because qualified to-test copies exist.

## Verification and upstream boundary

The integration is submitted through a separate fork PR and must have full backend
and frontend CI green before merging. Main's post-merge workflow is also checked.
The final PR body records exact tested heads, counts and workflow links. Local Docker
and WSL remain off; no unsuccessful local full-suite repeat is relabelled successful.

For upstream, [#16](https://github.com/Martinhdeez/zenithEnterprise/pull/16) and
[#17](https://github.com/Martinhdeez/zenithEnterprise/pull/17) are independent,
review-ready and have successful backend/frontend workflows. Martin still decides
whether to approve and merge them. The old fifteen PRs have no reported checks;
their existence does not imply that they passed the new CI. None is merged, closed,
retargeted or rewritten by this fork consolidation.

## Branch cleanup

Only branches whose exact heads are ancestors of the successfully merged fork main
are eligible for deletion, and source heads of any open upstream PR are excluded.
Retain an archive tag for every retired branch before removing its remote branch.
Preserve local worktrees, ignored datasets, models and logs. Unmerged historical
experiments remain available and are not silently promoted into the current product.

The two fork-only CI drafts for ingestion and relevance are incorporated into the
integration and can be closed with a link to the actual main merge. Their former
dedicated CI base can then be retired. Preserve the original seventeen upstream
source branches even when their work is also available in this fork's main.

The private-corpus product decision remains an optional, explicitly authorized mode;
the merge does not change default external-purpose flags or send private documents.
The next measured quality work is cited generated-answer support and abstention with
the corrected local comparator; the next ingestion investigation is the 77.50-second
persistence cost recorded in the single-file run.
