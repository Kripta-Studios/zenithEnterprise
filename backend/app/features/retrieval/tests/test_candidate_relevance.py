"""Corpus evidence survives reordering but cannot come from inaccessible documents."""

import json
from dataclasses import replace

import httpx

from app.core.hardware import PROFILES
from app.features.retrieval.relevance import Relevance
from app.features.retrieval.service import SearchService
from conftest import Account, WorkingEmbedder

from .test_rerank import reranker
from .test_search import profile_for, seed


def prefer_semantic(request: httpx.Request) -> httpx.Response:
    texts = json.loads(request.content)["texts"]
    return httpx.Response(
        200,
        json=[
            {"index": index, "score": 0.95 if body.startswith("Semantic") else 0.2}
            for index, body in enumerate(texts)
        ],
    )


async def test_semantic_selection_does_not_erase_authorized_lexical_evidence(
    account: Account,
) -> None:
    passages = [(f"The controller implements measure {i}.", i) for i in range(1, 5)] + [
        (f"Semantic paraphrase about safeguarding data, example {i}.", i) for i in range(5, 13)
    ]
    await seed(account.tenant_id, account.default_label, passages)
    service = SearchService(
        await profile_for(account),
        embedder=WorkingEmbedder(),  # type: ignore[arg-type]
        hardware=replace(PROFILES["cpu"], rerank_candidates=32),
        reranker=reranker(prefer_semantic),
    )
    for limit in (3, 8):
        result = await service.search("controller", limit=limit)
        assert result.relevance is Relevance.CONFIDENT
        assert len(result.hits) == limit
        assert all(hit.lexical_rank is None for hit in result.hits)
        assert not result.degraded


async def test_high_rerank_scores_cannot_admit_a_query_with_no_lexical_evidence(
    account: Account,
) -> None:
    await seed(account.tenant_id, account.default_label, [("Semantic data protection.", 1)])
    result = await SearchService(
        await profile_for(account),
        embedder=WorkingEmbedder(),  # type: ignore[arg-type]
        reranker=reranker(prefer_semantic),
    ).search("ZXQ-99817")
    assert result.relevance is Relevance.NONE
    assert not result.hits


async def test_another_tenants_lexical_matches_cannot_rescue_local_irrelevant_candidates(
    account: Account, other_account: Account
) -> None:
    await seed(account.tenant_id, account.default_label, [("Semantic data protection.", 1)])
    await seed(other_account.tenant_id, other_account.default_label, [("ZXQ-99817", 1)])
    result = await SearchService(
        await profile_for(account),
        embedder=WorkingEmbedder(),  # type: ignore[arg-type]
        reranker=reranker(prefer_semantic),
    ).search("ZXQ-99817")
    assert result.relevance is Relevance.NONE
    assert not result.hits
