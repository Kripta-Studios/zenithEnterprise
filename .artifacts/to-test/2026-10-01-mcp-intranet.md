# Optional intranet MCP boundary

Base: local MCP 5f590bb3f1ca24e4e20dafb2ee995636ab25f7eb; upstream main unchanged.
The user authorized completion of remaining work and delegated the identity-provider choice.
No schema changes or migration. Reuse existing read services, RLS and streaming uploads.

Implement a separately invoked loopback resource server, official SDK discovery/HTTP,
Keycloak introspection with fixed issuer/resource and explicitly enrolled subjects, current
Zenith permissions/token version, bounded transport/provider input and fail-closed behavior.
The local client/model and stdio entry point remain available. No automatic intranet exposure.

Checks: authenticated SDK TCP with real DB; invalid/expired/wrong issuer/audience/type/scope
tokens; provider failures; Host/Origin/body guards; current Zenith sign-out; real disposable
Keycloak PKCE/logout; real selected binary upload CLI, duplicate identity/hash and revocation.
Exact snapshots and raw check hashes are retained in the baseline branch's follow-up record.
