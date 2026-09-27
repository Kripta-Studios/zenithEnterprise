# Local v10 publication slice validation

These are local review refs. A result belongs only to the exact base, head and tree shown. No PR or remote CI exists. Every proposed slice is queued for Windows `make check`, a frontend production build, and `npm audit --omit=dev`; the final candidate has separate Linux and authenticated browser gates.

| Slice | Base | Exact head | Tree | Branch | Windows gate |
| --- | --- | --- | --- | --- | --- |
| foundation-prerequisite | `33b48812c95150348c52d2519159780252c92db2` | `5592601d1f1cb44333685c898e065d17dd9d99a5` | `822420f2d4c58178f2fbcfbf221dea97555681de` | `fix/evidence-v3-series-foundation-v10` | running; clean-install audit 0 in smoke |
| pr01-judge | `5592601d1f1cb44333685c898e065d17dd9d99a5` | `98f7935c3beedb0d9aea0e128ee6bc5adc86a2bf` | `714fe8491afdf4101f617b31ca56da99f21e4f56` | `fix/evidence-v3-series-pr01-v10` | pending |
| pr02-jev | `98f7935c3beedb0d9aea0e128ee6bc5adc86a2bf` | `9fa658f681ebde099cb0f641b432c1d5e620431d` | `a8bf28135d08f64c04acbedc7f0a769ca5c38559` | `fix/evidence-v3-series-pr02-v10` | pending |
| pr03-hybrid | `9fa658f681ebde099cb0f641b432c1d5e620431d` | `f408e26e903a4c8aaf92c6c9b26c82bd6d5453ee` | `1855b457c083458f1c34aa64fb9af03a15100c66` | `fix/evidence-v3-series-pr03-v10` | pending |
| pr04-direct | `f408e26e903a4c8aaf92c6c9b26c82bd6d5453ee` | `e1feb7b758fffca07d71975d75f7cc9822e04de3` | `eee3f7d6cac723540ced392604eac1fa03e213f7` | `fix/evidence-v3-series-pr04-v10` | pending |
| proxy-prerequisite | `e1feb7b758fffca07d71975d75f7cc9822e04de3` | `520d8e7c77b9408621c0d0db2c0d162ed17e1263` | `4e0dd7202f4684d597e5ee9d64a527422f15569e` | `fix/evidence-v3-series-prerequisite-v10` | pending |
| pr05-coverage-ui | `520d8e7c77b9408621c0d0db2c0d162ed17e1263` | `146bbf48f9e0bc9eaa4759fd23a56e30dfbf348f` | `a6649a9e14c22d83f13f6f4c38b19baa2fa7a5eb` | `fix/evidence-v3-series-pr05-v10` | pending |
| neutral-evaluation-prerequisite | `146bbf48f9e0bc9eaa4759fd23a56e30dfbf348f` | `45d2b75e68c423fec8b5886add59b4c69c533b95` | `419ca603b0e88a69a408cd0e1f67ba4fca537f3e` | `fix/evidence-v3-series-neutral-v10` | pending |
| pr06-packets | `45d2b75e68c423fec8b5886add59b4c69c533b95` | `76f2ba442aecdd92b4b21474c6ae0aab092c406e` | `ece779fc904abecaae1f1af839921e606656bb05` | `fix/evidence-v3-series-pr06-v10` | running |
| pr07-strict-support | `76f2ba442aecdd92b4b21474c6ae0aab092c406e` | `c17d1090d17940965b3bdbc763c55f29d9e03f35` | `0925a01ff41fe735aaf980abeda89918f6cb2d0f` | `fix/evidence-v3-series-pr07-v10` | pending |
| pr08-qualification-ui | `c17d1090d17940965b3bdbc763c55f29d9e03f35` | `9a2f69ffa56d9190c362cb9d0a14cd6e4ce85cf7` | `b06532618c8bc7f1ac6a91fac714b4c61f251d4d` | `fix/evidence-v3-series-pr08-v10` | pending |
| release-validation-report | `9a2f69ffa56d9190c362cb9d0a14cd6e4ce85cf7` | `1ba0239337bf762330ae48656cb1745af4085684` | `dd85a940276d8cd00cf90a88861acb43f352217f` | `fix/evidence-v3-series-release-v10` | pending |
| hardening-core | `1ba0239337bf762330ae48656cb1745af4085684` | `910bc125bb6f731ca681f20ac8ae19d97a5e0874` | `93a088dbf604811b938e5e73b18566937d200626` | `fix/evidence-v3-series-hardening-v10` | pending |

The first review slice carries the compatible production lockfile repair and Windows licence/frontend route together. A clean `npm ci` plus production audit at that tip exited 0 with zero advisories. This does not substitute for its full gate. PR06 contains the import-order fix before its own check.

Earlier v8 diagnostic attempts completed 898 backend tests with 11 skips at PR01 and 973 with 13 skips at PR06, but their `make check` stopped at the then-missing Windows licence route. V9 preparatory attempts were interrupted during recomposition and are not counted as passes. The earlier R1-free core tree `d69c37070fe22d0069804abea5708c835add8317` passed Windows and Linux full application-role suites and authenticated Windows browser acceptance. These results remain historical evidence, not inherited v10 qualifications.

Linux Ruff, format and Pyright already passed at the exact final v10 tree `93a088dbf604811b938e5e73b18566937d200626`. The exact v10 final backend/frontend/browser results will be entered from their own runs. No remote ref, PR, default, or deployment was changed.
