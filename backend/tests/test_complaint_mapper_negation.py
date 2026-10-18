import pytest

from app.models.severity_ml_service import _load_bundle
from app.models.complaint_mapper import ComplaintMapper


def _mapper() -> ComplaintMapper:
    bundle = _load_bundle()
    return ComplaintMapper(bundle.features.complaint_vec_.vocabulary_)


def test_negated_chest_pain_and_shortness_of_breath_map_only_headache():
    mapped = _mapper().map("no chest pain, no shortness of breath, mild headache")

    assert mapped == ["headache pain in head"]


def test_positive_chest_pain_and_shortness_of_breath_still_map_both():
    mapped = _mapper().map("chest pain and shortness of breath")

    assert "chest pain" in mapped
    assert any("shortness of breath" in term for term in mapped)


def test_denies_fever_cough_for_three_days_maps_cough_not_fever():
    mapped = _mapper().map("denies fever, cough for 3 days")

    assert "cough" in mapped
    assert "fever" not in mapped


def test_negation_does_not_cross_sentence_boundary():
    mapped = _mapper().map("no fever. chest pain")

    assert "chest pain" in mapped
    assert "fever" not in mapped


@pytest.mark.parametrize(
    ("text", "expected_present", "expected_absent"),
    [
        ("no fever. chest pain", ["chest pain"], ["fever"]),
        ("no cough, chest pain", ["chest pain"], ["cough"]),
        ("no chest pain but shortness of breath", ["shortness of breath"], ["chest pain"]),
        ("denies chest pain", [], ["chest pain"]),
        ("without fever", [], ["fever"]),
    ],
)
def test_negation_boundaries(text, expected_present, expected_absent):
    mapped = _mapper().map(text)

    for expected in expected_present:
        assert any(expected in term for term in mapped)
    for expected in expected_absent:
        assert all(expected not in term for term in mapped)


@pytest.mark.parametrize("text", ["no complaints", "denies pain", "no symptoms"])
def test_fully_negated_or_empty_signal_has_zero_coverage(text):
    mapper = _mapper()

    assert mapper.map(text) == []
    assert mapper.coverage(text) == 0.0


def test_approved_synonyms_are_whole_word_and_negation_aware():
    mapper = _mapper()

    mapped = mapper.map(
        "diarrhoea and vomiting, respiratory distress, confused and drowsy, sweating",
        approved_synonyms=True,
    )

    assert "diarrhea" in mapped
    assert "nausea and vomiting" in mapped
    assert "shortness of breath dyspnoea" in mapped
    assert "altered mental status confusion" in mapped
    assert "sweating diaphoresis" in mapped

    negated = mapper.map("no vomiting, no respiratory distress", approved_synonyms=True)
    assert "nausea and vomiting" not in negated
    assert "shortness of breath dyspnoea" not in negated

    negated_breathlessness = mapper.map("denies breathlessness", approved_synonyms=True)
    assert "shortness of breath dyspnoea" not in negated_breathlessness


def test_approved_synonym_path_respects_existing_negation_case():
    mapped = _mapper().map(
        "no chest pain, no shortness of breath, mild headache",
        approved_synonyms=True,
    )

    assert mapped == ["headache pain in head"]


def test_approved_synonyms_do_not_map_unapproved_generic_terms():
    mapped = _mapper().map(
        "generic weakness with wound fever cyanosis shock dehydration muscle pain leptospirosis",
        approved_synonyms=True,
    )

    assert "paralysis weakness one side hemiplegia" not in mapped
    assert "skin infection cellulitis" not in mapped
    assert all("fever" not in term for term in mapped)


def test_conditional_synonyms_are_separately_enabled():
    mapper = _mapper()

    assert "skin infection cellulitis" not in mapper.map("infected wound with pus")
    assert "diabetes management" not in mapper.map("ran out of insulin")
    assert "skin infection cellulitis" in mapper.map(
        "infected foot wound with pus",
        conditional_synonyms=["infected_wound"],
    )
    assert "diabetes management" in mapper.map(
        "ran out of insulin",
        conditional_synonyms=["insulin"],
    )


def test_danger_terms_are_negation_aware():
    mapper = _mapper()

    assert mapper.danger_terms("cough for two days, also unresponsive") == ["unresponsive"]
    assert mapper.danger_terms("cyanosis") == ["cyanosis"]
    assert mapper.danger_terms("no seizure") == []
