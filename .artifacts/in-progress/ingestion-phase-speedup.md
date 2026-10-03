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
