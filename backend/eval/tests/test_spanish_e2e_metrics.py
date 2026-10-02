"""A correct-looking answer cannot earn grounding credit for an unrelated citation."""

from copy import deepcopy

import pytest

from eval.spanish_e2e import measure, normalized, paired_interval, prepare, save, token_f1


@pytest.fixture
def example():
    case = {"answers": [{"text": "Madrid", "start": 20, "end": 26}]}
    hit = {
        "chunk_id": "chunk",
        "document_id": "document",
        "char_start": 0,
        "char_end": 40,
        "text": "La capital de España es Madrid.",
    }
    response = {"answer": "Madrid [1].", "citations": [hit], "abstained": False}
    return case, hit, response


def test_grounded_answer_requires_matching_actual_span(example):
    case, hit, response = example
    assert measure(case, response, [hit])["grounded_reference_match"] == 1
    wrong = deepcopy(response)
    wrong["citations"][0]["char_start"] = 30
    assert measure(case, wrong, [hit])["grounded_reference_match"] == 0


def test_valid_citation_to_wrong_source_does_not_support_correct_answer(example):
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


def test_uncited_or_abstained_answers_are_not_grounded(example):
    case, hit, response = example
    response["citations"] = []
    assert measure(case, response, [hit])["grounded_reference_match"] == 0
    response["abstained"] = True
    assert measure(case, response, [hit])["answer_token_f1"] == 0


def test_each_sentence_needs_a_marker(example):
    case, hit, response = example
    response["answer"] = "Madrid [1]. Tiene una población enorme."
    assert measure(case, response, [hit])["sentence_citation_coverage"] == 0.5
    assert measure(case, response, [hit])["grounded_reference_match"] == 0


def test_span_supported_extra_claim_is_not_semantically_certified(example):
    case, hit, response = example
    response["answer"] = "Madrid es la capital de todos los países [1]."
    assert measure(case, response, [hit])["grounded_reference_match"] == 1
    # This explicit limitation prevents presenting the lexical proxy as semantic correctness.
    assert measure(case, response, [hit])["answer_token_f1"] < 0.5


def test_normalization_retains_spanish_accents_and_answer_token_accounting():
    assert normalized("¡Álvaro! [1, 2]") == "álvaro"
    assert token_f1("la ciudad de Madrid [1].", "Madrid") == 0.4


def test_paired_interval_preserves_article_clusters():
    rows = [
        {"article": "same", "jev": {"x": 1}, "bge": {"x": 0}},
        {"article": "same", "jev": {"x": 0}, "bge": {"x": 1}},
    ]
    assert paired_interval(rows, "x")["ci95"] == [0, 0]


def test_dataset_overlap_is_rejected(tmp_path):
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
