# Inference and browser evidence matrix

| Lane | Exact evidence | Status |
| --- | --- | --- |
| Authenticated default browser | Historical `1862072e55f3d79877334964b0e1b3a8f473a39f` passed 11 checks. Fresh core candidate `4092f2735d30e7bc360bce88113c246eaf1fda60` passed 11: real login, application-role RLS, ingest, source download, text/PDF highlights, tenant/label checks and TEI. | passed at exact core tip |
| Authenticated experimental browser | Fresh core candidate passed 10 checks covering direct/packet/strict UI and fallback. Real auth/RLS/TEI and sources; generator scripted at model boundary, Jev disabled. | passed at exact core tip for scripted-generation lane |
| Local concurrent search | Fresh core candidate: 12 requests with six workers; all HTTP 200, no degradation, 12 isolation assertions, p50 4,980 ms and max 6,546 ms on local fixture. | passed narrow local lane; no provider capacity claim |
| Real Jev ranking versus local TEI | Initial 10 queries in English, Spanish, French, Portuguese, and German: both top-1 10/10. Follow-up 10 in Italian, Dutch, Polish, Catalan, and Japanese: TEI 20/20 combined; Jev pairwise 18/18 assessed, bundled Noul 19/19, Choice 19/19, with two bundle failures. | exploratory only; no advantage established; [architecture probe](jev-atomic-options-probe.md) |
| Real Jev Score | New 48 calls, 47 valid; one raw 0.99-mass response. | partial; Score contract unresolved |
| Real Jev strict support | New 24 self-authored claims, 11/12 supported accepted and 0/12 unsupported accepted at default threshold. | exploratory; independent calibration absent |
| Real generator plus real Jev, authenticated | No combined live end-to-end run in this pass yet. Historical scripted generator and separate real Jev calls are distinct lanes. | not_run |
| Real generator plus strict support | No independently labeled matched answer trial. | not_run |
| Sustained provider concurrency | Two tiny four-pair serial versus two-wide batches only. | not_run for sustained load |
| Linux frontend clean install/types/tests/build/audit | Archived exact core candidate `4092f2735d30e7bc360bce88113c246eaf1fda60` in disposable Node 24.21.0 Bookworm container: `npm ci`, TypeScript lint, 450/450 Vitest in 43 files, production build, production audit; all exited 0, audit zero vulnerabilities. One earlier concurrent run timed out a single LabelPicker test at five seconds; isolated full rerun passed. | passed for frontend only |
| Linux backend/application-role DB | Archived exact core candidate on WSL Ubuntu 24.04, Python 3.12.3: Ruff, format and Pyright passed; 1,004 backend tests passed, 14 skipped, using disposable ParadeDB/PostgreSQL and application roles. | passed at exact code tree |
| Linux authenticated browser | No Linux browser run; the exact-tip authenticated browser ran on Windows with real auth/RLS/TEI. | not_run |

The exact candidate browser logs, random fixture and screenshots remain ignored locally; their evidence index SHA-256 is `18fceca70a5df53cbe43346dbe3c174b46e758ceb67bb4313c5417fdfdc6d96d`. The synthetic multilingual fixture is [tracked](../../backend/eval/fixtures/evidence-v3-multilingual-synthetic-pilot.json) for reproducibility. It is self-authored exploratory data, not private enterprise text or a new locked human-labeled test. Raw Score bodies and live ledgers remain ignored locally. No model was enabled by default.
