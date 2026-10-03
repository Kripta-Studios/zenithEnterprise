"""Bounded reads under current per-user authority, shared by MCP handlers."""

from dataclasses import asdict
from uuid import UUID

from sqlalchemy import select

from app.common.exceptions import AuthenticationError, NotFoundError
from app.core.database import tenant_session
from app.core.security import decode_token
from app.features.auth.access.dependencies import requires
from app.features.auth.model import User
from app.features.auth.service import AccessProfile, AuthService
from app.features.documents.model import Chunk, Document
from app.features.documents.schemas import DocumentResponse
from app.features.documents.service import DocumentService
from app.features.retrieval.schemas import HitResponse, SearchResponse
from app.features.retrieval.service import EXECUTE, SearchService

MAX_HITS = 8
MAX_EXCERPT = 2000
MAX_SOURCE = 8000


class LocalReads:
    def __init__(self, token: str) -> None:
        self._token = token

    async def profile(self, permission: str | None = None) -> AccessProfile:
        auth = AuthService()
        user_id, tenant_id = auth.principal(self._token)
        profile = await auth.profile(user_id, tenant_id)
        # A long-lived stdio process does not cache a login or accept a removed user.
        # This transport checks the existing version column on every operation. REST's
        # stateless access-token expiry window is unchanged.
        payload = decode_token(self._token, "access")
        async with tenant_session(profile.context) as session:
            version = await session.scalar(select(User.token_version).where(User.id == user_id))
        if version is None or version != payload.get("ver"):
            raise AuthenticationError("invalid credentials")
        if permission is not None:
            await requires(permission)(profile)
        return profile

    async def search(
        self,
        query: str,
        limit: int,
        labels: list[UUID] | None,
        documents: list[UUID] | None,
    ) -> dict[str, object]:
        if not 1 <= limit <= MAX_HITS or not 1 <= len(query) <= 1000:
            raise ValueError("invalid search bounds")
        if any(scope is not None and len(scope) > 16 for scope in (labels, documents)):
            raise ValueError("invalid scope bounds")
        profile = await self.profile(EXECUTE)
        result = await SearchService(profile).search(query, limit, labels, documents)
        profile = await self.profile(EXECUTE)
        # Search may wait for inference. A label/user revoked during that wait cannot
        # disclose a previously visible passage. Both sides of the join remain under RLS.
        async with tenant_session(profile.context) as session:
            visible = set(
                await session.scalars(
                    select(Chunk.id)
                    .join(Document, Document.id == Chunk.document_id)
                    .where(
                        Chunk.id.in_([hit.chunk_id for hit in result.hits]),
                        Document.status == "ready",
                    )
                )
            )
        hits: list[dict[str, object]] = []
        for hit in result.hits:
            if hit.chunk_id not in visible:
                continue
            item = HitResponse(**asdict(hit)).model_dump(mode="json")
            item["text"] = hit.text[:MAX_EXCERPT]
            item["truncated"] = len(hit.text) > MAX_EXCERPT
            item["excerpt_char_end"] = hit.char_start + len(str(item["text"]))
            item["coordinate_unit"] = "page" if hit.page_num is not None else "document"
            item["source_id"] = str(hit.chunk_id)
            item["content_kind"] = "extracted_original"
            item["bboxes_scope"] = "whole_chunk"
            item["bboxes"] = hit.bboxes[:128]
            item["bboxes_truncated"] = len(hit.bboxes) > 128
            item["filename"] = hit.filename[:512]
            item["metadata_truncated"] = len(hit.filename) > 512 or len(hit.label_ids) > 64
            item["label_ids"] = item["label_ids"][:64]
            hits.append(item)
        envelope = SearchResponse(
            hits=[],
            degraded=result.degraded,
            reason=result.reason,
            took_ms=result.took_ms,
            relevance=result.relevance.value,
        ).model_dump(mode="json")
        envelope["hits"] = hits
        envelope["coverage"] = "bounded retrieved passages; not complete corpus coverage"
        envelope["withheld_after_search"] = len(result.hits) - len(hits)
        return envelope

    async def source(self, source_id: UUID, offset: int, length: int) -> dict[str, object]:
        if not 0 <= offset <= 1_000_000 or not 1 <= length <= MAX_SOURCE:
            raise ValueError("invalid source bounds")
        profile = await self.profile(EXECUTE)
        async with tenant_session(profile.context) as session:
            row = (
                await session.execute(
                    select(Chunk, Document)
                    .join(Document, Document.id == Chunk.document_id)
                    .where(Chunk.id == source_id, Document.status == "ready")
                )
            ).first()
            if row is None:
                raise NotFoundError("no such source")
            chunk, document = row
            if offset > len(chunk.text):
                raise NotFoundError("no such source range")
            excerpt = chunk.text[offset : offset + length]
            return {
                "source_id": str(chunk.id),
                "document_id": str(document.id),
                "document_sha256": document.sha256,
                "filename": document.filename[:512],
                "media_type": document.media_type,
                "page_num": chunk.page_num,
                "coordinate_unit": "page" if chunk.page_num is not None else "document",
                "char_start": chunk.char_start + offset,
                "char_end": chunk.char_start + offset + len(excerpt),
                "text": excerpt,
                "truncated": offset + len(excerpt) < len(chunk.text),
                "content_kind": "extracted_original",
                "bboxes": chunk.bboxes[:128],
                "bboxes_scope": "whole_chunk",
                "bboxes_truncated": len(chunk.bboxes) > 128,
            }

    async def document(self, document_id: UUID) -> dict[str, object]:
        profile = await self.profile()
        document = await DocumentService(profile).get(document_id)
        # Metadata/status follows the existing authenticated REST read policy, including
        # the uploader's exception while processing. There is no new read permission.
        item = DocumentResponse.model_validate(document).model_dump(mode="json")
        # Parser/provider diagnostics can contain local paths. Keep status, omit detail.
        item.pop("status_detail", None)
        item["filename"] = document.filename[:512]
        item["description"] = document.description[:2000] if document.description else None
        item["label_ids"] = [str(label) for label in document.label_ids[:64]]
        item["metadata_truncated"] = (
            len(document.filename) > 512
            or len(document.description or "") > 2000
            or len(document.label_ids) > 64
        )
        return item
