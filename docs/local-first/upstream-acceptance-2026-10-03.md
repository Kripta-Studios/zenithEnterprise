# Independent upstream delivery and actual CI

The two changes Martin selected are now separate, review-ready pull requests against
`Martinhdeez/zenithEnterprise` main. Each immediate parent is upstream commit
`33b48812c95150348c52d2519159780252c92db2`. Neither imports Jev, the other slice,
or the v10 foundation. The original fifteen pull requests remain open and unmodified;
no branch was rewritten and nothing was merged.

| Slice | Upstream PR | Exact tested head | Backend | Frontend |
| --- | --- | --- | --- | --- |
| Provider-neutral local judge contract | [#16](https://github.com/Martinhdeez/zenithEnterprise/pull/16) | `36f4f7d7155dee047d9eb8f9528de312ba3b59d7` | 901 passed, 11 skipped, 165.94 s | 437 passed, 43 files |
| Vite proxy-prefix regression guard | [#17](https://github.com/Martinhdeez/zenithEnterprise/pull/17) | `9e9bd377dbdad1b3912c4b8aa147c2f8009e7cd2` | 886 passed, 11 skipped, 140.96 s | 437 passed, 43 files |

The [contract workflow](https://github.com/Martinhdeez/zenithEnterprise/actions/runs/37134724777)
and [proxy workflow](https://github.com/Martinhdeez/zenithEnterprise/actions/runs/37134728181)
both completed successfully, including backend lint, format, strict types and licenses.
The contract introduces provider-neutral backend cases. The proxy changes one
backend integration test file that reads the Vite configuration; it exercises every
required proxy prefix, including
the regression in which an omitted prefix returns SPA HTML rather than a 404.

Both PRs have `isDraft=false`, `state=OPEN`, and both required check runs report
`SUCCESS` at their exact heads. This fulfills Martin's request for independent slices
and evidence from his pipeline. It does not assert maintainer approval or authorize
merging: human review and the upstream adoption decision are still pending.

## Local evidence and retained failures

Two fresh full local Docker repeats were attempted concurrently on the shared laptop.
They timed out at 1,200 seconds, at approximately 71% and 72% progress, and their owned
containers were stopped. Wrapper times were 1,204.423 and 1,203.350 seconds. Those runs
are **failed local checks**, not substitutes for successful checks. The PR bodies retain
that limitation alongside the actual green upstream runs. No unchanged full local
suite was rerun merely to overwrite this evidence.

The subsequent independent ingestion and relevance branches are separate fork work:

- `fix/large-document-embedding-inserts`: three real application-role PostgreSQL
  regressions passed in 314.34 seconds at `c071653fefc8b0ec3a44af6e44dbfb66a01c0dbf`;
  the wrapper took 339.716 seconds. An earlier run passed the nineteen existing
  pipeline cases and two new rollback cases but lacked the second-tenant fixture.
  After that fixture was corrected, a Docker engine outage caused exit 125; the
  successful final three-case rerun is the qualification of the corrected tests.
- `fix/relevance-before-rerank-gate`: eighteen PostgreSQL relevance and isolation
  cases passed in 160.97 seconds at `7c7c02aeddebb6f620af62259407650c0c7f3658`;
  the wrapper took 184.682 seconds. An earlier run passed forty-two cases and had
  the same missing second-tenant fixture, which was then corrected and rerun.

Changed production files and feature tests passed Ruff, format checks and strict
Linux-target Pyright. The plan notes retain the `.artifacts/to-test/` status; focused
checks alone are not advertised as a complete local `make check`.

[Fork ingestion draft #2](https://github.com/Kripta-Studios/zenithEnterprise/pull/2)
and [fork relevance draft #3](https://github.com/Kripta-Studios/zenithEnterprise/pull/3)
use a new `ci/upstream-main-2026-10-03` base pinned to the same upstream revision.
This permits their full CI without moving either repository's main branch or adding
requirements to upstream PRs #16 and #17. Their draft status does not represent
upstream promotion, and no existing PR was closed or merged.

Both fork drafts also completed their full backend/frontend workflows successfully:

| Fork change | Exact CI head | Backend | Frontend | Workflow |
| --- | --- | --- | --- | --- |
| Bounded inserts | `021ebefe46904b4807d2edcadce0ff22f25bd329` | 885 passed, 11 skipped, 169.57 s | 437 passed, 43 files | [37138917161](https://github.com/Kripta-Studios/zenithEnterprise/actions/runs/37138917161) |
| Candidate gate | `d8eb50e6f3b44b7ef3b26691211ae9dc427d3ae9` | 885 passed, 11 skipped, 155.82 s | 437 passed, 43 files | [37138927986](https://github.com/Kripta-Studios/zenithEnterprise/actions/runs/37138927986) |

Those are full remote checks at the published heads, including strict types and
licenses; they do not turn an unsuccessful local full-suite repeat into a pass.

The separate model-backed fresh-question and single-file measurement is recorded in
[the local validation report](local-gate-and-ingestion-results-2026-10-03.md).
