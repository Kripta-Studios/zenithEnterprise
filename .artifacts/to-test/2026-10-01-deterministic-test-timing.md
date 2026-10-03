# Deterministic asynchronous and filesystem tests

Independent base: Martinhdeez main 33b48812c95150348c52d2519159780252c92db2.
No dependency on the two accepted extractions, v10, Jev or MCP.

The upload-queue test controls a deferred first completion and explicitly observes three
later files finishing before it is released. It tests concurrency/completion ordering
without relying on 1/30 ms timer scheduling under Windows or loaded CI workers.
Vitest uses an explicit one-to-two worker range to bound test residency on shared laptops.
This changes test execution only, not upload scheduling or application concurrency.

The read-only-checkout test explicitly changes the mtime by one second after restoring a
file's original bytes. The size/mtime guard remains intact; coarse filesystem clocks no
longer decide whether its intended mutation occurred. No runtime guard is weakened.

Validation: Node 22.23.3, 43 test files / 437 tests passed in 470.15 seconds; real Linux
checkout tests 6 passed in 11.77 seconds. Full build and types are recorded separately.
No dependency upgrades, schema changes or migrations.
