# Local-first groundwork

Independent base: upstream main 33b48812c95150348c52d2519159780252c92db2.
This branch contains local measurement/data tooling and decision records only. Neither
accepted extraction depends on it. No product defaults, network MCP endpoint, inference
provider or vector schema are changed.

Use existing uploads, deduplication, ingestion, TEI batch planners, requeue and GPU Compose.
Record measured failures as well as completed work. Keep raw public datasets and temporary
runner logs outside tracked code. Require separate authorization for remote publication.
