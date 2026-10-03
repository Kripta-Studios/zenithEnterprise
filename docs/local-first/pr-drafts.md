# Standalone local PR drafts — not published

Both parents are Martinhdeez main 33b48812c95150348c52d2519159780252c92db2,
freshly fetched before extraction. Neither requires the other, the benchmark branch,
the v10 foundation or Jev. The existing fifteen upstream PRs remain untouched.

## Draft 1: Extract the provider-neutral local judge contract

When search reranks candidates, TEI scores currently refer only to list indexes.
This change introduces a small typed candidate/assessment boundary and uses it in the
existing local search path through a TEI adapter. Source identities, repeated text,
batching, stable ties and fused fallback remain intact. Malformed or incomplete
assessments fall back as a whole; cancellation propagates and one deadline bounds
the sequential rerank batches.

This independently replaces the logical judge contribution of
[old upstream #2](https://github.com/Martinhdeez/zenithEnterprise/pull/2).
It has no Jev client, foundation history, API/schema/dependency/default change.
The historical increment spanned twelve files; this extraction limits the product
change to five implementation files, one contract test file and the repository's plan note.

Local validation: 29 focused tests passed against disposable ParadeDB with the
application role; six public Spanish fixtures gave byte-identical IDs/scores through
legacy and adapted real CPU TEI. Lint, format, Linux types, shipped-license check,
frontend types and build pass. Full backend: 900 passed, 11 skipped, one failure in
the unchanged timestamp-based checkout test. Full frontend: 436 passed, one failure
in the unchanged upload queue timing test. These failures are retained, not fixed
inside this extraction. Remote Actions have not run for this local commit.

Candidate: feat/local-judge-contract-standalone,
36f4f7d7155dee047d9eb8f9528de312ba3b59d7; tree
839b36ca7075969e9e108d2feaebf611d850bfec.

## Draft 2: Guard Vite proxy prefix coverage in CI

A development API prefix omitted from Vite can return the SPA HTML instead of JSON.
This one-file test change reads the actual proxy object, checks its configured
prefixes and literal/declared API targets, ignores unrelated fetch strings and keeps
the existing Nginx and intentionally omitted-prefix checks. It proves a missing
`/search` fails coverage even if an unrelated string mentions that route.

This independently replaces the logical guard contribution of
[old upstream #6](https://github.com/Martinhdeez/zenithEnterprise/pull/6).
It is a CI prefix-coverage regression guard. No Vite configuration, runtime target
validator, route, dependency or product default is added.

Local validation: seven focused tests pass. Actual Vite with the unchanged config
proxies all twelve prefixes to a local JSON fixture and serves intentional omissions
as SPA HTML. Lint, format, Linux types, shipped-license check, frontend types and build
pass. Full backend: 885 passed, 11 skipped, one unchanged checkout timestamp-test
failure. Full frontend: 436 passed, one unchanged Analytics async-render failure.
Remote Actions have not run for this local commit.

Candidate: fix/vite-proxy-prefix-guard-standalone,
9e9bd377dbdad1b3912c4b8aa147c2f8009e7cd2; tree
e488ce8393928392c8442b540fd79c77e9f646bd.

## Publication steps requiring separate authorization

1. Inspect the two exact local commits and resolve or separately attribute the retained
   baseline test failures. Fetch upstream again and check each proposed base is current.
2. If the base moved, prepare new separately reviewable candidates without rewriting
   published branches. Repeat the checks for those exact candidates.
3. Push only the two named standalone branches after explicit permission. Create two
   independent PRs with these descriptions; do not invent future PR numbers.
4. Ask the maintainer to approve fork Actions if required and inspect actual remote
   results. Approval to run Actions does not authorize a merge.
5. Only with separate permission, add links marking old #2/#6 as logically superseded
   according to Martin's preference. Do not close, rewrite or merge the old series.

## Spanish reply for Martin — not sent

Gracias, Martín. He preparado localmente el contrato del judge y el guard de prefijos
como dos cambios independientes desde tu main, sin el stack v10 ni Jev. Los checks
focalizados pasan; los suites completos conservan los fallos de los tests de timestamps
y de temporización del frontend, que detallo en el informe. No he publicado ni cambiado
ninguna PR existente.

He comprobado la paridad del adaptador con TEI CPU y medido la subida hasta pending,
incluida la deduplicación. El servicio GPU no alcanzó readiness en el intento acotado;
por eso todavía no presento cifras de upload-to-ready ni una mejora CPU/GPU. El siguiente
paso medido es aislar ese arranque del backend GPU antes de tocar lotes o concurrencia.
Para MCP propongo empezar con cliente y modelo locales, mantener las subidas por REST
autenticado y usar Keycloak si después desplegamos el endpoint en intranet.
