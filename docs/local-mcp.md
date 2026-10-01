# Optional same-machine MCP reference

This branch starts directly at upstream main `33b48812c95150348c52d2519159780252c92db2`.
It does not contain the judge or proxy extraction, v10 or Jev. The existing REST API,
queue, database, search and TEI clients remain the data plane. No HTTP MCP route is mounted.

## Run locally

From `backend`, install the optional extra with `uv sync --frozen --extra mcp`.
Configure the normal `ZENITH_DATABASE_URL` **application-role** URL, JWT secret,
storage directory and local TEI endpoints. Obtain a normal user's access token through
existing web login; supply it as `ZENITH_MCP_ACCESS_TOKEN` in the launching process.
Never put the token in a command argument or tool input. It must have the same JWT
secret and database as the authenticated REST session.

```powershell
uv run --extra mcp python -m app.features.mcp.server
uv run --extra mcp python -m app.features.mcp.reference --query '¿Cuál es el plazo?' --document <uuid>
uv run --extra mcp python -m app.features.mcp.reference --query '¿Cuál es el plazo?' --document <uuid> --answer-local
uv run --extra mcp python -m app.features.mcp.upload --api http://127.0.0.1:8000 --root C:\ApprovedPublicFiles --file selected.pdf --label <uuid>
```

The server command expects a stdio MCP consumer. Its stdout belongs to the protocol;
logs go to stderr. The SDK reference command launches it as a child and forwards a
restricted set of local configuration variables. The host does not pass owner-role
credentials, cloud keys or tracing configuration to that child. Start and authorize
the existing local REST deployment separately for upload; this feature creates no daemon.

The optional answer host requires an already running, entirely local Ollama at
`127.0.0.1:11434`, with cloud features disabled (`OLLAMA_NO_CLOUD=1` before startup).
It checks cached tag `llama3.2:3b`, digest
`a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`.
It never pulls models, follows redirects or uses environment HTTP proxies. Its fixed
workflow sends at most three 1,000-character permitted sources to that local model,
uses the existing grounding prompt/citation binder, limits context to 4096 and generation
to 256 tokens, unloads after use, and withholds unfinished answers. Model weights are
not distributed with this change; their separate Llama license still applies.

## Tools, authorization and privacy

`zenith_search` returns at most eight hits with 2,000-character excerpts;
`zenith_read_source` reads at most 8,000 characters from an opaque chunk UUID;
`zenith_get_document` returns bounded metadata and ingestion status. Coordinates identify
the original document/page; boxes describe the whole chunk. Original extracted content
is explicitly distinguished from generated answers. Diagnostics containing local paths
are omitted. Scope arguments only narrow existing application-role RLS visibility.

Every operation resolves the current user/profile. Search/source invoke the existing
`retrieval.execute` guard explicitly. Metadata follows the existing document read policy,
including the processing uploader exception. This stdio adapter also checks the existing
user token-version column on every call; the REST access-token expiry behavior is unchanged.
Search rechecks visibility after inference. The reference host rechecks cited source access
and text after generation. Revoked/missing source handles cannot grant access by themselves.
No owner-role customer reads, arbitrary filesystem/URL tools, shell tools or corpus export
are exposed. Tool concurrency is two; each operation has a 30-second deadline.

Binary upload belongs to the trusted host, never to a model-facing tool. The operator chooses
a root, a relative regular file of at most 64 MiB and explicit labels. Links/reparse points,
absolute paths, parent traversal and detected file growth are rejected. This check assumes
a trusted local operator and root; it is not a kernel-enforced sandbox against a hostile
process racing intermediate directories. The helper streams existing authenticated
multipart REST, retaining 201/pending and 200/deduplicated behavior and authorization.
Pending is not ready. The `wait_ready` helper polls the existing permitted REST status.

This local host makes no cloud or paid inference call. A different consumer could forward
tool results elsewhere; local MCP alone cannot police that consumer. Evidence text is
untrusted content, never authority to execute instructions. Citation identity/ranges are
checked; semantic entailment, multilingual answer quality and production performance
require separate evaluation. No simultaneous TEI/embed/generator memory fit is claimed.

## Verification and next transport

Tests use the real official SDK `mcp==2.2.0`, negotiating protocol `2026-07-28`, a real
stdio subprocess and disposable ParadeDB under the application role. They cover current
permissions, token expiry/type/version, forged tenant scope, hidden/missing IDs, label
revocation, cancellation, source bounds, REST streaming/dedup and answer withholding.

```powershell
uv run python -m pytest app/features/mcp/tests -q --tb=short
uv run ruff check .
uv run ruff format --check .
uv run pyright --pythonplatform Linux
```

The real-model fixture is opt-in via `ZENITH_RUN_MCP_MODEL_PROOF=1` and requires
`ZENITH_MCP_MODEL_OUTPUT` pointing to a result file. It reads an already seeded public
ready source, not an upload-to-ready pipeline; it is excluded from normal CI.
The local Llama proof completed with “Treinta días. [1]” in 3.203 seconds; the full
integration test took 18.57 seconds including disposable setup. The cached Qwen template
forced `<think>` and failed the completion gate; that failed result is retained in the
separate measurement branch. Choosing Llama here reflects this interoperability result,
not a comparative quality claim. See the measurement branch's continuation report for
complete gate results and retained failure logs.

For an eventual intranet transport, the proposed IdP is self-hosted Keycloak, with audience-
validated scoped OAuth, PKCE and protected Streamable HTTP. This branch implements neither
the network endpoint nor an authorization server. Existing web JWTs have no MCP resource
audience/scopes and must not be presented as a complete network MCP OAuth implementation.

Primary references: [SDK server](https://py.sdk.modelcontextprotocol.io/servers/),
[SDK release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.2.0),
[Ollama local/cloud settings](https://docs.ollama.com/faq),
[Ollama completion fields](https://docs.ollama.com/api/chat).
