# Local v9 publication slice validation

These are local candidate refs. A result belongs only to the exact head and tree shown. No PR or remote CI exists. The full Windows gate for each slice is `make check`, a frontend production build, and `npm audit --omit=dev`; the audit is expected to expose inherited advisories until the integrated security slice.

| Slice | Base | Exact head | Tree | Branch | Windows gate |
| --- | --- | --- | --- | --- | --- |
| portability-prerequisite | `33b48812c95150348c52d2519159780252c92db2` | `cc92f01e8736e6de1cbd4fae1a7303bb2f3c04e7` | `db06d22adb384f90d132847693fd078d6470de35` | `fix/evidence-v3-series-portability-v9` | running or pending; see final results |
| pr01-judge | `cc92f01e8736e6de1cbd4fae1a7303bb2f3c04e7` | `b65fc470bbc514040d032c3d4b15ff121d688f30` | `021946c2fd98a28c556ad44581159be4bcbb51d9` | `fix/evidence-v3-series-pr01-v9` | running or pending; see final results |
| pr02-jev | `b65fc470bbc514040d032c3d4b15ff121d688f30` | `1f0dd1fd12802030472d37b3b193081c62d19fa3` | `365cb7dc6348b002e43dd68656f3b8d522fc8c34` | `fix/evidence-v3-series-pr02-v9` | running or pending; see final results |
| pr03-hybrid | `1f0dd1fd12802030472d37b3b193081c62d19fa3` | `273df29b42d02504516b4caf169d635764b1d82d` | `a082f77f3f0bf4f57759d08142f9eda7ecbf7a7e` | `fix/evidence-v3-series-pr03-v9` | running or pending; see final results |
| pr04-direct | `273df29b42d02504516b4caf169d635764b1d82d` | `e050c308f4ca23e8f5ea523649a98bc767ceb188` | `a1988b9bd4168e8a46feef14dc0b7e8808767a46` | `fix/evidence-v3-series-pr04-v9` | running or pending; see final results |
| proxy-prerequisite | `e050c308f4ca23e8f5ea523649a98bc767ceb188` | `4a9e9cde92af79c658eda32160f5702630430b23` | `d5e31ad5ed8acf0e64522d0ef580fa617645aa34` | `fix/evidence-v3-series-prerequisite-v9` | running or pending; see final results |
| pr05-coverage-ui | `4a9e9cde92af79c658eda32160f5702630430b23` | `6425c01045a559d472320a82d889cbb713533805` | `26b0ceddba5833112c9f0c448e53c1b7ed321287` | `fix/evidence-v3-series-pr05-v9` | running or pending; see final results |
| neutral-evaluation-prerequisite | `6425c01045a559d472320a82d889cbb713533805` | `1dd18c3e6d21a0b8499474f864b977eb011c4668` | `bb8f6ce41b630d3ceacd3e390c29375c7046c7a5` | `fix/evidence-v3-series-neutral-v9` | running or pending; see final results |
| pr06-packets | `1dd18c3e6d21a0b8499474f864b977eb011c4668` | `c1d5424b77791289d2ecafe53d01073223e32c4b` | `49095f52bb87a9054f4acb8b443d1ff3e53cde2b` | `fix/evidence-v3-series-pr06-v9` | running or pending; see final results |
| pr07-strict-support | `c1d5424b77791289d2ecafe53d01073223e32c4b` | `ddb6fc5958f61a7b040ccbdbcaeafd5e16208e72` | `70b39392924d4c0e1c9d59b8a8c13ac2bfe922dd` | `fix/evidence-v3-series-pr07-v9` | running or pending; see final results |
| pr08-qualification-ui | `ddb6fc5958f61a7b040ccbdbcaeafd5e16208e72` | `e253f300738ff08503168f8ea825b7aaac5765d5` | `21dcd221b25595787f460e807251100a0c898988` | `fix/evidence-v3-series-pr08-v9` | running or pending; see final results |
| integrated-security | `e253f300738ff08503168f8ea825b7aaac5765d5` | `0a94ed4d6b61acfe92338b33d1381d7e734454f4` | `b06532618c8bc7f1ac6a91fac714b4c61f251d4d` | `fix/evidence-v3-series-security-v9` | running or pending; see final results |
| release-validation-report | `0a94ed4d6b61acfe92338b33d1381d7e734454f4` | `b7302ebf66109c929bbb2d2e231aba6c30f9a9af` | `dd85a940276d8cd00cf90a88861acb43f352217f` | `fix/evidence-v3-series-release-v9` | running or pending; see final results |
| hardening-core | `b7302ebf66109c929bbb2d2e231aba6c30f9a9af` | `7e446fd7927022eedfc15dde8d7c61d1e7bfcacd` | `93a088dbf604811b938e5e73b18566937d200626` | `fix/evidence-v3-series-hardening-v9` | running or pending; see final results |

V8 diagnostic attempts are not counted as full passes: PR01 completed 898 backend tests with 11 skips, and PR06 completed 973 with 13 skips, but their `make check` stopped at the Windows licence stage because the early tips lacked the Windows route. V9 puts the route before PR01. At the v9 PR01 tip, separate licence and frontend smoke checks passed (437 frontend tests in 43 files); its complete exact-tip gate remains in the queue.

Linux Ruff, format and Pyright passed at final tree `93a088dbf604811b938e5e73b18566937d200626`. The earlier R1-free core tree `d69c37070fe22d0069804abea5708c835add8317` passed Windows and Linux full application-role suites and authenticated Windows browser acceptance. Those results remain historical evidence and are not silently inherited by any v9 tip. The exact v9 final Linux/backend/browser status will be updated from its own runs.

No remote ref, PR, default, or deployment was changed.
