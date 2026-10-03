# Resolve measured non-persistence ingestion time

Base: fork main cf46383b123bedcc4dc2e402790c7e848cec73b3.

Instrument an actual fresh 844643-byte / 938-chunk public upload with real cached
BAAI/bge-m3 GPU embeddings. Separate parsing, routing/chunking, status writes,
embedding requests/tokenization/queue/compute, persistence and classification.
Use the previous memory-safe 1024-token/two-item service as the diagnostic comparator.

Optimize only the measured dominant phase. Preserve sequential request ordering,
profile/server agreement, CPU/low-spec safety, source text, full vectors, RLS,
one atomic persistence transaction, upload streaming, deduplication and retry behavior.
Reuse the existing GPU override and local cached model; no paid/provider calls.

Run alternating paired fresh uploads against matched document layout and service
settings, retaining raw phases and resource measurements. Verify all chunks, source
coordinates and vectors; quantify any float16 batch numerical effects rather than
claiming bitwise equality across batch shapes. Run actual embedding/ingestion tests
and complete backend/frontend checks before authorized fork-main integration.
Preserve all upstream PRs. Stop owned services, Docker Desktop and WSL after operations.

Completed: diagnostic fresh upload, preliminary bounded tuning, eight actual paired
GPU uploads (one warmup pair and three measured pairs), full source/vector integrity
checks, and a source-free reproducible report. Embedding median falls 62.579710 to
29.176888 seconds; ready falls 93.420162 to 59.270400 seconds. Persistence did not
improve in this task. Profile `gpu-local` and the existing Blackwell overlay deliver
matching 4096/eight limits to both application processes and TEI services.

Validation: 24 focused host tests pass; strict Pyright has zero errors. Full fork
backend/frontend CI remains the integration gate. A full local make check is not
claimed; the user's request to close Docker/WSL takes precedence over retaining
them for a duplicate full suite. Both are off after completing GPU operations.

Report: docs/local-first/ingestion-phase-results-2026-10-03.md with JSON/CSV artifact
bindings. Next measurement: vector serialization/index/commit versus the now-balanced
embedding phase, preserving atomic replacement and RLS. No provider calls or downloads.

First full Linux CI: 1085 passed, 29 skipped, two test-fixture failures. Resolve
Compose against a complete temporary installation and make the existing lexical
candidate-evidence guard use real exact dense SQL rather than depend on synthetic
ANN recall in a shared database. No production retrieval changes or weakened
assertions. The six updated Compose checks pass locally; full CI is repeated.
