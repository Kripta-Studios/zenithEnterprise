"""A correct-looking answer cannot earn grounding credit for an unrelated citation."""

from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from eval.spanish_e2e import measure, normalized, paired_interval, prepare, save, token_f1
from eval.spanish_e2e_nli import apply_entailment, claim_inputs

Example = tuple[dict[str, Any], dict[str, Any], dict[str, Any]]


def test_atomic_snapshot_survives_a_transient_host_read_lock(tmp_path: Path) -> None:
    target = tmp_path / "progress.json"
    original = Path.replace
    calls = 0

    def replace(source: Path, destination: Path) -> Path:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError("transient Docker Desktop host read lock")
        return original(source, destination)

    with patch.object(Path, "replace", replace), patch("eval.spanish_e2e.time.sleep"):
        save(target, {"complete": True})
    assert calls == 2 and '"complete": true' in target.read_text(encoding="utf-8")


@pytest.fixture
def example() -> Example:
    case = {"answers": [{"text": "Madrid", "start": 24, "end": 30}]}
    hit = {
        "chunk_id": "chunk",
        "document_id": "document",
        "char_start": 0,
        "char_end": 40,
        "text": "La capital de España es Madrid.",
    }
    response = {"answer": "Madrid [1].", "citations": [{**hit, "marker": 1}], "abstained": False}
    return case, hit, response


def test_grounded_answer_requires_matching_actual_span(example: Example) -> None:
    case, hit, response = example
    assert measure(case, response, [hit])["grounded_reference_match"] == 1
    wrong = deepcopy(response)
    wrong["citations"][0]["char_start"] = 30
    assert measure(case, wrong, [hit])["grounded_reference_match"] == 0


def test_valid_citation_to_wrong_source_does_not_support_correct_answer(example: Example) -> None:
    case, _, response = example
    unrelated = {
        "chunk_id": "other",
        "document_id": "document",
        "char_start": 100,
        "char_end": 140,
        "text": "Madrid fue sede de una conferencia.",
    }
    response["citations"] = [unrelated]
    metric = measure(case, response, [unrelated])
    assert metric["reference_match"] == 1
    assert metric["invalid_citations"] == 0
    assert metric["grounded_reference_match"] == 0


def test_uncited_or_abstained_answers_are_not_grounded(example: Example) -> None:
    case, hit, response = example
    response["citations"] = []
    assert measure(case, response, [hit])["grounded_reference_match"] == 0
    response["abstained"] = True
    assert measure(case, response, [hit])["answer_token_f1"] == 0


def test_same_reference_text_and_offsets_in_another_file_are_not_grounded(example: Example) -> None:
    case, hit, response = example
    case["filename"] = "correct.txt"
    hit["filename"] = "other.txt"
    response["citations"][0]["filename"] = "other.txt"
    metrics = measure(case, response, [hit])
    assert metrics["reference_match"] == 1
    assert metrics["invalid_citations"] == 0
    assert metrics["grounded_reference_match"] == 0


def test_each_sentence_needs_a_marker(example: Example) -> None:
    case, hit, response = example
    response["answer"] = "Madrid [1]. Tiene una población enorme."
    assert measure(case, response, [hit])["sentence_citation_coverage"] == 0.5
    assert measure(case, response, [hit])["grounded_reference_match"] == 0


def test_span_supported_extra_claim_is_not_semantically_certified(example: Example) -> None:
    case, hit, response = example
    response["answer"] = "Madrid es la capital de todos los países [1]."
    assert measure(case, response, [hit])["grounded_reference_match"] == 1
    # This explicit limitation prevents presenting the lexical proxy as semantic correctness.
    assert measure(case, response, [hit])["answer_token_f1"] < 0.5


def test_normalization_retains_spanish_accents_and_answer_token_accounting() -> None:
    assert normalized("¡Álvaro! [1, 2]") == "álvaro"
    assert token_f1("la ciudad de Madrid [1].", "Madrid") == 0.4


def test_paired_interval_preserves_article_clusters() -> None:
    rows = [
        {"article": "same", "jev": {"x": 1}, "bge": {"x": 0}},
        {"article": "same", "jev": {"x": 0}, "bge": {"x": 1}},
    ]
    assert paired_interval(rows, "x")["ci95"] == [0, 0]


def test_dataset_overlap_is_rejected(tmp_path: Path) -> None:
    data = {
        "data": [
            {
                "title": "Public",
                "paragraphs": [
                    {
                        "context": "Madrid",
                        "qas": [
                            {
                                "id": "q",
                                "question": "¿Dónde?",
                                "answers": [{"text": "Madrid", "answer_start": 0}],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    dev, test = tmp_path / "dev.json", tmp_path / "test.json"
    save(dev, data)
    save(test, data)
    with pytest.raises(ValueError, match="overlap"):
        prepare(dev, test, tmp_path / "panel.json", test_count=1)


def test_independent_entailment_rejects_unsupported_extra_claim(example: Example) -> None:
    case, hit, response = example
    response["answer"] = "Madrid es la capital de todos los países [1]."
    span = measure(case, response, [hit])
    assert span["grounded_reference_match"] == 1
    assert apply_entailment(span, [0.1], 0.8)["entailed_grounded_reference_match"] == 0
    assert apply_entailment(span, [], 0.8)["entailed_grounded_reference_match"] == 0
    with pytest.raises(ValueError, match="probability"):
        apply_entailment(span, [float("nan")], 0.8)


def test_independent_judge_receives_only_the_cited_source(example: Example) -> None:
    _, hit, response = example
    claims = claim_inputs(response)
    assert len(claims) == 1
    assert claims[0]["premise"] == hit["text"]
    assert claims[0]["claim"] == "Madrid ."
