# Bound large-document embedding inserts

Base: current upstream main 33b48812c95150348c52d2519159780252c92db2.
Branch: fix/large-document-embedding-inserts, independent of the judge, proxy and Jev.

The public 650-context ingestion hit the existing PostgreSQL statement timeout when
939 vectors were flushed together. Bound embedding INSERT flushes to 64 vectors per
statement group, while retaining the single transaction for replacement pages, chunks,
vectors and classifying status. Do not raise the timeout or commit partial documents.
Keep existing streaming uploads, hash deduplication, TEI batching, RLS and classification.

Verify large text/vector alignment and labels under the application role, idempotent
re-ingestion, and rollback after an invalid vector beyond the first batch. Measure the
original full public corpus as one file, including persistence and upload-to-ready;
record exact source head and retain failures. No migration or model/default change.

Independent application-role PostgreSQL run at
c071653fefc8b0ec3a44af6e44dbfb66a01c0dbf: 3 passed in 314.34 seconds,
including vector alignment, tenant/label denial, idempotence, and rollback after
two flushed batches. The existing pipeline suite also passed 19 tests in the earlier
run; its missing second-tenant fixture was corrected and the new tests rerun.
Ruff/format and strict Linux-target Pyright passed on changed source and tests.
Retain the Docker engine outage and full-suite local timeouts in the delivery record;
the focused checks do not claim a full local make check. The model-backed single-file
measurement lives in the separate research branch and is not a runtime dependency.
