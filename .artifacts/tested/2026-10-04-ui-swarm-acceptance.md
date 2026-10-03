# Zenith UI swarm acceptance — 2026-10-04

Status: local acceptance completed. The associated fork PR runs the final aggregate Linux CI gate.

Base: fork main `e49fd78e225c4176d4e439b502fa6d5d61f85127`.
The user requested actual UI checks for existing and newly integrated functionality.
Seven implementation/test lanes and one independent read-only review used one isolated checkout, assigned file ownership, disposable
tenants and public synthetic documents. The supported Chrome connection was broken;
the user explicitly requested Playwright. Tests used Playwright 1.63.0 and installed
Chrome 154.0.8037.95 with isolated headless contexts, without personal browser profiles.

## Real workflow coverage

| Area | Actual evidence and outcome |
| --- | --- |
| Authentication and navigation | 18/18 browser scenarios passed; 5/5 affected translation/accessibility replays passed. Login errors, keyboard entry, invitation redemption/reuse, password change, profile edits, local/global sign-out, command palette, language/theme persistence and 1440/768/390-pixel initial Search shell. Zero uncaught page errors. |
| Document workflows | Real PDF/TXT uploads, display title/description, duplicate feedback, source bytes, PDF paging/zoom, text preview, parser failure details and owned-document delete/cancel verified. |
| Large-document integrity | One actual 180-page PDF reached ready, with 360 unique chunks and 360 finite unit-normalized 1024-dimensional vectors. Stored source SHA matches the upload; source offsets and labels are consistent. Independently reembedded all 360 chunks, minimum matching cosine 0.9999822974. Application-role RLS returns no unscoped chunks and all 360 correctly scoped chunks. |
| Native bulk selection and ingestion | 52 actual fresh HTTP uploads, unique IDs and filenames; all 52 reached ready with one real page/chunk/vector each. Every stored source SHA matches. Pagination passed 50 initial rows + 11 cursor rows, including all 52 batch documents. Public-label scope excludes restricted Finance. |
| Upload label response | Initial successful bulk POSTs exposed stale nested label metadata. After a real API restart, 3/3 fresh/changed-duplicate/quarantine HTTP checks pass: nested metadata equals wire labels and the authenticated GET. |
| Administration | Nine panels render; real role create/edit/delete, label search/sort/merge preview/cancel/in-use delete refusal, profile edits, reset-link issuance/redemption/reuse refusal, local connector save, and tenant create/suspend/reactivate/name-confirmation guards verified. Additional owned-label replay passes 4/4 with zero page errors: two creations 201, rename HTTP 200 (no UI rename control exists), UI merge preview/commit 200 and UI delete 204. All five original labels survive; both temporary labels were removed. |
| Group consistency | 7/7 actual browser checks pass with zero page errors. Creation/deletion refresh Groups, Access matrix and People and groups without navigation; valid drafts survive and deleted-group drafts cannot affect another group. Three fresh group creations returned 201; six deletions returned 204 including prior owned harness cleanup. |
| Immediate permissions and isolation | Same-token actual grant/revoke sequences pass: roles endpoint 403→200→403, private source 404→200→404, file access 200→404, and zero assigned roles yields no permissions or system authority. Cross-tenant/label/file refusals and system-admin boundary verified. |
| MCP | 22/22 actual SDK/HTTP/database checks pass in 49.359 seconds. Two fresh streamed TXT uploads reached ready; nine advertised tools/resources/prompt, ordered batch sources, character coordinates, limits, stdio transport, TCP OAuth boundary and session/label revocation verified. Keycloak introspection was mocked; the TCP SDK transport and database were real. Reranking was explicitly degraded in this embedding-only window. |
| Search and Spanish cited generation | 19/19 actual browser checks pass: genuine nondegraded BGE Standard ranking, Direct and Auto complete unchanged 5/5 scope receipts, Hybrid shortlist receipt, ranking controls, source fullscreen, local Spanish 30-day answer with a clickable bound citation, correct support-team follow-up, unknown-question abstention with empty final prose, persisted history/re-ask, exact TXT highlight and nonsense-search withholding. Zero browser exceptions. |
| Installed-queue tenant purge | Initial owned-empty-tenant purge returned 202 but failed in the real worker: platform role cannot update owner-installed queue tables. Corrected production task replay succeeded: tenant purged, real job 83 succeeded, all 81 neighbor-job statuses unchanged. Fresh-worker harness 13.079 seconds; no grants or tenant status reset. |
| Compiled production bundle | Six distinct acceptance checks completed against the final compiled bundle: exact built index/assets, real login, navigation/new chooser, corrected Spanish profile, exact original TXT and painted PDF canvas with lazy viewer/worker assets. Zero page/console errors. Four initial checks in 30.063 seconds; source-only replay 4/4 in 19.859 seconds, after correcting an ambiguous harness selector. |

The rows group overlapping scenarios; they must not be added into a fabricated total.
Browser workflows and integration/component test counts are separate evidence.

## Confirmed defects and corrections

1. An upload's display title chose the parser, rejecting legitimate text titles without
   a suffix. The router now passes the original source filename independently. Original
   source/byte format validation and spoof rejection remain enforced.
2. Trigger-written `document.label_ids` was stale in fresh upload and changed duplicate
   responses. Refresh only that field through the existing tenant-bound RLS session.
3. Deduplicated ready uploads appeared as new documents and duplicated recent rows.
   Preserve the response flag, show Already present, and keep rows unique by ID. Existing
   failed documents remain failures.
4. The native chooser advertised only PDF. Advertise the PDF/TXT/Markdown formats and
   suffix aliases the existing ingestion service supports.
5. Resetting the native file input emptied its live FileList before React processed the
   deferred updater. Snapshot the files synchronously. A mutable-file-list regression
   reproduces the original lifetime; 52 actual native-selected files now stage correctly.
6. Role creation and clearance options sent zero while the unchanged API requires 1–10.
   Use the minimum valid level and expose only valid options; no permissions are added.
7. A denied initial model-configuration read caused an unhandled promise rejection.
   Render the refusal and retry; ignore stale success/failure after token changes.
8. Group creation/deletion left the access and membership panels stale. Refresh their
   catalogs, preserve valid drafts, prune obsolete group IDs and guard late responses.
9. Profile/session and credential-link security explanations remained English in Spanish
   mode; invitation validation lacked an alert role and account-email spacing. Translate
   the explanations/errors and announce validation through the existing UI mechanisms.
10. Installed-queue tenant purge could not cancel queued jobs using the platform role.
    Use the established owner connection only for queue cancellation; customer-row
    deletion remains on the restricted platform connection with the same tenant predicate.
    No new queue grants. Real installed-queue regression initially failed with the exact
    privilege error; corrected installed-queue regression passed in 87.76 seconds and
    production-worker replay purged the owned target successfully. All 13 existing
    lifecycle tests passed. The intermediate test-only result-materialization error is
    preserved separately from the original product failure.

No migration, dependency, paid-provider integration, isolation policy or production
feature default was changed by these UI corrections.

## Automated gates

Final locked frontend source: 474 tests across 47 files have passing assertions across
two runs. The aggregate Windows run passed 464 tests/46 files but exited 1 because
Vitest could not start the Analytics worker; the missing file passed 10/10 independently
in 13.54 seconds, exit 0. Do not label the aggregate command green. Locked Vitest is
4.1.11. Final TypeScript passes, and production build passes in 45.56 seconds.

Compiled-bundle source manifest SHA-256:
`47146f63f2f24c94e8f2150d1af26e38a8d3d5000aa5fd490300db40979170e9`.
Artifact manifest SHA-256:
`bd719943749b4b99d03515511d7838d597d1664059b665c724fad9512430d761`.

The pre-correction full frontend baseline passed 450/450; it is retained as baseline,
not substituted for the corrected-source checks. An initial shared-node_modules
Vitest version mismatch and other worker-start failures remain in the raw evidence.

Final whole-backend Ruff lint/format passes (398 Python files); strict Pyright reports
0 errors and 0 warnings. The complete Windows PostgreSQL suite finished with 1095
passed, 29 skipped and one failure in 2388.87 seconds, exit 1. The sole failure is
`test_selected_binary_upload_over_tcp_and_cli`: the Windows Selector event loop
required by psycopg cannot implement `asyncio.create_subprocess_exec`. This is a
test-launcher portability failure, not a skipped CLI assertion or an accepted green run.
The correction uses a bounded standard-library subprocess through a worker thread,
keeping actual loopback HTTP and all upload/deduplication/hash/secret/permission assertions.
The corrected-source fresh-PostgreSQL replay passed 1/1 in 110.91 seconds, exit 0.
The aggregate source remained unchanged throughout its run (461-file manifest SHA-256
`0d60d77b51b910ac66ba47ef70dbb087b771b203f96097aea0eac5dbd617b932`).
The original aggregate result and the corrected-source replay are retained separately;
Linux CI remains the final complete-suite check on the corrected test source.
The corrected replay's before/after 461-file source manifest also matches:
`6aea0e833fd5252463ebe624574c2a0fa558c1263250f0ff4e6b936a8b1b2f74`.
Whole-backend Ruff lint/format and strict Pyright were repeated after this change:
all pass, with 0 type errors and 0 warnings.

Five parser cases skipped for an absent BERT fixture were subsequently run against
the cached original PDF, verified against its pinned SHA-256
`5692a5514787a8c6727b4ff3b726a3385798bc68e12138d1d4af83947e2acf6e`.
That focused run passed 5 tests with 2 GDPR-fixture skips in 57.53 seconds. The
original 29 aggregate skips remain recorded; this replay does not rewrite that result.
The exact GDPR fixture is unavailable, as are other complete-corpus checks. Optional
paid/Jev, real Keycloak, separate model and performance benchmarks remain opt-in.
The shipped-dependency licence check passed. Focused GPU Compose/retry checks passed
24/24; pure MCP authorization, citation and relevance checks passed 42/42. Model-backed
UI generation is separate from the 26 existing citation/prompt/streaming regressions.

## Resource handling and limits

The primary runtime used ParadeDB/PostgreSQL 17, actual migrations through 0027,
application and platform roles, a concurrency-one worker, cached BGE-M3 embedding,
cached BGE-reranker-v2-m3 and local llama3.2:3b. Optional direct/packet features were
enabled only in the QA environment. Jev/external-processing paths stayed disabled.
There were zero paid/Jev calls and zero new model downloads.

Three host-RAM guard interruptions stopped only owned model services. Initial and
aborted runs are preserved. Browser windows were serialized, clean WSL page-cache
reclaim restored headroom, and the guard retains its 1536 MiB free-host floor.
Unrelated training and native services were untouched.

The large PDF's observed 122.115-second worker duration is functional evidence under
shared load, not a paired performance benchmark or regression against an earlier TXT
baseline. A tiny local 3B generator verifies application behavior; it does not establish
production answer quality or Jev superiority. The MCP check does not prove a deployed
Keycloak server. Only Chromium was tested; responsive coverage is the initial shell.
Access-token expiry was not waited for; sign-out-everywhere does not promise immediate
invalidation of already issued stateless access tokens. Member Admin navigation still
offers operations the server refuses; this is a remaining usability limitation.
The search PDF's settled screenshot shows real aligned amber bounding-box overlays.
Generated-citation checks assert the bound document/page opening; their screenshots
did not wait for a settled overlay, so they do not assert that additional visual condition.
The independent read-only final diff review found no actionable correctness/security blocker.

## Evidence and reproduction

Ignored local evidence is retained under `.local-evidence/` in the isolated QA checkout:
`zenithEnterprise-v3-clean/.scratch/zenith-ui-swarm/`, relative to the KriptaStudios directory.
Lane reports: `auth_navigation/report.md`, `documents_ingestion/LANE_RESULTS.md`,
`admin_isolation/REPORT.md`, `admin_group_refresh/focused-tests.md`, search report,
`regressions/gates.json`, and runtime integrity/resource/cleanup JSON.
Raw browser traces, initial failures, command logs and source hash bindings remain
local; they are not published wholesale because traces can contain disposable session
credentials. This checked-in report contains no account passwords or tokens.
Changed source bytes and normalized Git blob IDs are recorded in
`2026-10-04-ui-swarm-source-bindings.json`. Physical hashes describe the QA worktree;
Git blob IDs account for the checkout's Windows line-ending normalization.

Final reproducible gates: backend `ruff check .`, `ruff format --check .`, strict
`pyright`, and `pytest -q --tb=short` against fresh actual PostgreSQL; frontend
`npm ci`, `npm run lint`, `npm test -- --maxWorkers=1 --pool=threads`, isolated
Analytics replay, and `npm run build`; the repository shipped-licence script.
Windows pytest uses the repository Windows-selector bootstrap and UTF-8 mode.

All owned UI/API/worker/model processes were stopped and the disposable UI database
was removed after their checks. Docker Desktop's normal stop exhausted its deadline;
the supported `--force` stop subsequently completed with exit 0. No manual process
kill was needed. `wsl --shutdown` completed with exit 0: Docker processes and vmmemWSL
are absent and no WSL distributions remain running. Containers/volumes were preserved;
unrelated native services/training were untouched. Cleanup records remain under
`runtime/desktop-shutdown-before.json` and the final shutdown manifest.
Fork publication and integration require the associated Linux CI to pass.
Existing upstream PRs are preserved unchanged.
