"""Opt-in alternating fresh uploads with identical corpus and resident GPU services."""

import json
import os
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest
from sqlalchemy import text

from app.core.config import settings
from app.core.database import tenant_session
from app.features.retrieval.tests.test_search import profile_for
from conftest import Account
from eval.tests.test_spanish_e2e_pipeline import postgres as postgres
from eval.tests.test_spanish_e2e_pipeline import test_public_spanish_answers as run_upload

pytestmark = pytest.mark.skipif(
    not os.environ.get("ZENITH_RUN_INGESTION_PHASE_SERIES"), reason="opt-in paired GPU ingestion"
)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, trial_index: int) -> Path:
    root = Path(os.environ["ZENITH_E2E_OUTPUT"])
    arm = "baseline" if trial_index in (0, 3, 4, 7) else "candidate"
    output = root / f"trial-{trial_index}-{arm}"
    output.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ZENITH_E2E_OUTPUT", str(output))
    monkeypatch.setenv("ZENITH_E2E_EMBED_URL", f"http://embed-{arm}:80")
    monkeypatch.setenv("ZENITH_E2E_HARDWARE", "gpu-local")
    if arm == "baseline":
        monkeypatch.setenv("ZENITH_E2E_BATCH_TOKENS", "1024")
        monkeypatch.setenv("ZENITH_E2E_BATCH_ITEMS", "2")
    else:
        monkeypatch.delenv("ZENITH_E2E_BATCH_TOKENS", raising=False)
        monkeypatch.delenv("ZENITH_E2E_BATCH_ITEMS", raising=False)
    monkeypatch.setattr(settings, "storage_dir", tmp_path / "documents")
    return output


@pytest.mark.parametrize("trial_index", range(8))
async def test_paired_fresh_ingestion(
    trial_index: int,
    isolated_storage: Path,
    account: Account,
    owner_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = isolated_storage
    await run_upload(account, owner_url, monkeypatch)
    record = json.loads((output / "capture-results.json").read_text())
    assert record["upload"]["chunks"] == 938
    assert len(record["upload"]["documents"]) == 1
    assert record["upload"]["documents"][0]["http_status"] == 201
    binding = json.loads((output / "embedding-source-bindings.json").read_text())
    array: npt.NDArray[np.float32] = np.load(output / "embedding-vectors.npy", allow_pickle=False)
    assert array.shape == (938, 1024) and np.isfinite(array).all()
    # Verify actual application-role stored text/ranges, labels and full vectors.
    profile = await profile_for(account)
    async with tenant_session(profile.context) as session:
        rows = (
            await session.execute(
                text(
                    "SELECT c.text, c.page_num, c.char_start, c.char_end, c.label_ids, "
                    "e.embedding::text AS vector FROM chunks c JOIN chunk_embeddings e "
                    "ON e.chunk_id=c.id AND e.tenant_id=c.tenant_id ORDER BY c.char_start,c.id"
                )
            )
        ).all()
    assert len(rows) == 938
    import hashlib

    for index, row in enumerate(rows):
        assert binding[index] == {
            "sha256": hashlib.sha256(row.text.encode()).hexdigest(),
            "page_num": row.page_num,
            "char_start": row.char_start,
            "char_end": row.char_end,
        }
        assert row.label_ids == [account.finance_label]
        assert np.array_equal(np.asarray(json.loads(row.vector), dtype=np.float32), array[index])
    reference_dir = output.parent / "trial-0-baseline"
    reference: npt.NDArray[np.float32] = np.load(
        reference_dir / "embedding-vectors.npy", allow_pickle=False
    )
    assert binding == json.loads((reference_dir / "embedding-source-bindings.json").read_text())
    norms: npt.NDArray[np.float32] = np.linalg.norm(array, axis=1)
    assert np.allclose(norms, 1, atol=1e-4)
    cosine = np.asarray(
        np.sum(array * reference, axis=1) / (norms * np.linalg.norm(reference, axis=1)),
        dtype=np.float64,
    )
    assert float(cosine.min()) >= 0.9999
    (output / "vector-integrity.json").write_text(
        json.dumps(
            {
                "trial": trial_index,
                "warmup": trial_index < 2,
                "sources_and_coordinates_equal": True,
                "stored_vectors_equal": True,
                "minimum_cosine_to_warmup": float(cosine.min()),
                "maximum_absolute_difference": float(np.max(np.abs(array - reference))),
            },
            indent=2,
        )
    )
