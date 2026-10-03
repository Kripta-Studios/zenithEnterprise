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

Focused checks: three readiness, one child-exit, two score-resume and one UTF-8 regression pass; twelve
existing Spanish metric/citation/entailment tests pass; the changed pipeline module
passes strict Linux-target pyright with the actual dependency interpreter. Ruff passes.
Actual upload/retrieval, interruption/resume, generated-query audit and the complete
128-pair NLI result now pass as measured evidence, rather than being inferred from these
unit tests. The successful integration head is 2c563142db1551ef5eb68174b23694a2a8af5fb2;
pytest reports one passed in 963.67 seconds, wrapper exit zero in 983.86 seconds.

The first persistent attempt uploaded fourteen documents / 939 chunks in 199.385 seconds
and captured all 144 queries. It reused 4,334 exact pairs and scored 274 new pairs per
arm. Jev's cumulative ledger reached 15,175 calls / $0.385689192 estimated input cost.
Ten actual generated pairs completed before the harness's per-question logins hit the
unchanged login limiter. Preserve that failure; use normal refresh-token rotation on a
ten-minute cadence. Reuse fully completed score stages only after exact panel-hash,
question-set and finite complete-score validation. No paid-stage replay is needed.

The first resume failed on Windows locale decoding of a Spanish path; all JSON reads
now explicitly use UTF-8. The final resume validated all 144 actual retrieval captures,
completed all 128 pairs and graded them independently. Jev's primary result is 20/128,
BGE's 10/128, paired CI [0.015503875968992248, 0.14728682170542637]. Meaningful gain
passes; clearly-larger gain fails. The existing lexical gate blocks 75 BGE questions
despite correct evidence in their eight passages. See the complete result and limits in
[the measured report](../../docs/local-first/spanish-e2e-results-2026-10-03.md).
