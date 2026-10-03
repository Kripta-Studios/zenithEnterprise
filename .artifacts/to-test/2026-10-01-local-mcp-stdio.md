# Local MCP proof

Base: upstream/main 33b48812c95150348c52d2519159780252c92db2.
Implement an optional, local stdio transport after the user's instruction to continue.
Keep the accepted extractions independent. No network listener, OAuth service, cloud model,
paid reranker, product-default change or remote publication.

Reuse AuthService, the REST permission guard, SearchService, DocumentService and app-role
RLS. Resolve credentials and labels on every call; recheck search visibility before return.
Bound search/source responses. Expose search, source fragment and metadata/status only.
Keep uploads in authenticated multipart REST. Pin the official SDK as an optional extra.

Verify actual SDK protocol calls and stdio subprocess, real disposable ParadeDB/RLS,
permission/label revocation, hidden/nonexistent IDs, forged scope, expiry/revocation,
source bounds, cancellation and safe errors. Run lint, strict types and affected checks.
Record local-model interoperability separately from the no-model protocol proof.
