# First MCP client, transport and identity decision

Status: local-first direction accepted by the user on 2026-10-01; network implementation
is a later stage. No MCP endpoint or authorization service has been installed.

Zenith will be an MCP server exposing its existing retrieval, sources and document status.
It will not become a general agent host or client of arbitrary servers. The first consumer
must run locally with a local model, as selected by the user. Propose a scripted official SDK
reference client first, using the already cached Ollama qwen3:4b Q4_K_M model. Its manifest
SHA-256 is 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7;
all declared local blobs exist (2,497,293,931 bytes). This is a small local candidate for
the first protocol proof, not a claim of best answer quality. Ollama's localhost service
was not running during inspection. No generation model was started and simultaneous GPU
residency remains unqualified. The interactive host, binary transfer and tool invocation
compatibility still need a concrete integration test. No new model or cloud call is needed.

For the same-machine proof, prefer stdio with explicit per-user application credentials
and current AccessProfile resolution, without a network auth service. This is a proposed
transport choice, not tested interoperability. The local host must not send tool results,
telemetry or traces containing sources to a cloud model. A local server alone cannot enforce
the consumer's downstream processing destination.

For a later intranet deployment, propose self-hosted Keycloak rather than building OAuth
inside Zenith. No existing organizational IdP was identified; the user delegated the choice.
Keycloak's OIDC discovery, signing keys, authorization-code flow, introspection and revocation
make it suitable for an on-premises identity boundary. Configure authorization code plus PKCE,
pre-registered clients, resource audience and minimal scopes. An operator must confirm issuer,
principal mapping, deployment ownership and token/revocation policy before implementation.

Zenith's current HS256 web tokens contain sub, tid, ver, typ, iat and exp. They do not declare
MCP resource audience or OAuth scopes, and web login/refresh is not a complete MCP OAuth
authorization server. Refresh checks token_version; existing access sessions can survive until
expiry. Keep these facts explicit rather than claiming instantaneous token revocation.

For HTTP MCP, use protected Streamable HTTP with TLS at the deployment boundary, Origin
checks, protected resource metadata and audience-validated expiring tokens. Pin an SDK version
that actually supports the selected client protocol. Propose official Python SDK mcp==2.2.0
for the reference client/server, with protocol revision 2026-07-28. Its published release notes
describe that revision's connections, but this checkout has no interoperability result yet.
No SDK has been added to the application lockfile. Test the pinned client's initialize handshake,
negotiated revision, cancellation, audience rejection and expired-session recovery before release.

Direct MCP service calls must explicitly check operation permissions and refresh AccessProfile.
REST dependency checks do not run automatically outside the router. Use zenith_app for customer
content; never expose queue owner credentials or treat a tenant argument as authority. Recheck
source access after search and after label revocation. Return bounded source IDs/coordinates;
avoid raw filesystem paths, arbitrary URLs, SQL, commands or corpus-export tools.

Binary uploads remain authenticated multipart POST /documents. The trusted host streams a
user-selected file with explicit labels, then polls permitted document status. MCP is the
control plane, not a base64 PDF channel. No interactive client's binary-transfer capability has
been verified yet; use the existing web uploader until it is. New uploads return 201, duplicates
200; both precede readiness and duplicates can change labels.

Sources checked on 2026-10-01:
- https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
- https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
- https://github.com/modelcontextprotocol/python-sdk
- https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.2.0
- https://www.keycloak.org/securing-apps/oidc-layers
- https://ollama.com/library/qwen3:4b
- upstream backend/app/core/security.py, auth/service.py, auth/access/dependencies.py,
  documents/router.py and retrieval/service.py at the recorded base.
