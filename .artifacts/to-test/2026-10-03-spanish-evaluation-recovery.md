# Recover the frozen Spanish answer/citation evaluation

Base: c9f8ad0 on perf/spanish-e2e-citations. Neither accepted extraction changes.

The old controller used a 180-second model deadline and destroyed its disposable
database after interruption. Preserve one explicitly owned PostgreSQL container/volume,
fixture identity, test account, original document storage and capture across attempts.
On resume, recheck authorized document IDs and all actual retrieval candidates. Reuse
only exact recorded question/source scores; retain cumulative paid reservations.

Use a configurable bounded model deadline (initially 900 seconds), health/identity plus
a neutral real inference, resource sampling before startup and cleanup of owned services.
Propagate the actual pytest failure exit. Preserve old failed records and per-attempt logs.

The cohort, generator digest/options, production prompt, 32-to-eight candidates, frozen
Jev criterion, citation rules and NLI threshold do not change. Partial GPU residency is
an explicit execution option for shared hardware, recorded rather than presented as an
isolated online latency benchmark. No unrelated training process is suspended or stopped.

Focused checks before the actual run: three readiness regressions and one child-exit
propagation regression pass; twelve
existing Spanish metric/citation/entailment tests pass; the changed pipeline module
passes strict Linux-target pyright with the actual dependency interpreter. Ruff passes.
Actual upload/retrieval, interruption/resume, generated-query audit and the complete
128-pair NLI result remain required run evidence, not inferred from these unit tests.
