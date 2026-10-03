# Corrected local baseline, persistence and agent reads

Base: fork main d12620a8cd973e5f2d1012900a63f1726b225e05.

Repeat the frozen 128 Spanish generated-answer pairs through actual query and citation
audit writes using the corrected shared local relevance gate. Reuse scores only for
identical question/passage inputs and generation only for identical complete requests.
Retain independent multilingual NLI, original thresholds and all historical evidence.
This repeat measures the corrected baseline; it is not a fresh unseen holdout.

Profile real public 938-chunk persistence before choosing an optimization. Preserve a
single atomic transaction, full vectors, row-level security, labels and retry behavior.
Compare repeated runs on identical hardware and vectors, recording SQL phase timings.

Extend existing local and authenticated network MCP reads with bounded corpus discovery,
batched source reads and ingestion status. Preserve fresh authority per operation, local
inference and revocation checks. Validate real SDK calls, RLS, pagination and output bounds.
No arbitrary URL/filesystem imports or general agent framework.

Publish only to the fork after checks. Preserve all upstream PRs and source branches.

Implementation and all three measured experiments are complete. Results and next
experiments: docs/local-first/corrected-baseline-continuation-2026-10-03.md.
Focused application-role checks pass: 22 atomic ingestion, 54 MCP (3 optional skips),
three opt-in performance checks and the 128-pair integration/independent grading.
The complete local backend runner timed out; full GitHub checks are required before
fork-main integration. Docker and WSL are stopped at the user's explicit request.
