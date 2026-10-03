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
