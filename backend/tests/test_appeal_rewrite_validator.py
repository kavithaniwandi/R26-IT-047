"""Offline admission checks for grammatical rewrites and factual anchor changes."""
import logging

import pytest

from app.models import appeal_rewrite_validator as validator

ORIGINAL = (
    "Every child deserves a safe place to sleep and a hot meal to start the day. "
    "Yet hundreds of families in our immediate community go without these basic necessities every single night. "
    "When a crisis hits—whether it is an unexpected medical bill or a sudden job loss—the stability of an entire household can shatter in an instant. "
    "By joining hands with us today, your generosity can provide the emergency food packages, warm clothing, and critical shelter support that vulnerable families need to rebuild their lives. "
    "Your contribution is more than just financial aid; it is a powerful message of hope, reminding our neighbors that they are not forgotten and that a caring community is standing right beside them."
)
REWRITE = (
    "Every child deserves a safe place to sleep and a hot meal to start the day. "
    "Yet, hundreds of families in our immediate community go without these basic necessities every single night. "
    "When a crisis hits, such as an unexpected medical bill or a sudden job loss, the stability of an entire household can shatter in an instant. "
    "Your generosity can provide emergency food packages, warm clothing, and critical shelter support that vulnerable families need to rebuild their lives. "
    "Your contribution reminds our neighbors that they are not forgotten and that a caring community stands right beside them."
)
SCHOLARSHIP = (
    "Brilliant students from low-income families are being forced to abandon their dreams of a college education simply because they cannot afford the cost of tuition and textbooks. "
    "Academic talent is everywhere, but equal opportunity is not, leaving thousands of capable young minds locked out of the future they worked so hard to build. "
    "Your gift to our scholarship fund breaks down these financial barriers, directly providing the tuition assistance, mentorship, and resources hard-working students need to stay in school and graduate."
)
SCHOLARSHIP_REWRITE = (
    "Brilliant students from low-income families are being forced to abandon their dreams of a college education because they cannot afford tuition and textbooks. "
    "Academic talent is everywhere, but equal opportunity is not. This leaves thousands of capable young minds locked out of the future they worked hard to build. "
    "Your gift to our scholarship fund breaks down these financial barriers. It directly provides the tuition assistance, mentorship, and resources hard-working students need to stay in school and graduate. "
    "Please consider supporting these students."
)


def test_scholarship_rewrite_allows_sentence_splitting_and_grounded_action():
    assert validator.validate_rewrite(SCHOLARSHIP, SCHOLARSHIP_REWRITE).accepted
    unsafe = SCHOLARSHIP_REWRITE.replace("these students.", "these students today.")
    assert validator.validate_rewrite(SCHOLARSHIP, unsafe).reason == "changed_deadline_or_urgency"


@pytest.mark.parametrize("original,rewrite,accepted", [
    ("We need water. Our neighbors are not forgotten.", "We need water.", True),
    ("Our neighbors are not forgotten.", "Our neighbors are forgotten.", False),
    ("Our neighbors are not forgotten.", "Our neighbors are not forgotten.", True),
    ("Our neighbors are not forgotten.", "Our neighbors are never forgotten.", False),
    ("Students need tuition assistance.", "Please support students.", True),
    ("Students need tuition assistance.", "Please support patients.", False),
    ("Students need tuition assistance.", "Please support students with medicine.", False),
    ("Your generosity can provide food.", "Your generosity provides food.", False),
])
def test_clause_omission_requests_and_meaning_preservation(original, rewrite, accepted):
    assert validator.validate_rewrite(original, rewrite).accepted is accepted


def test_recorded_grammatical_rewrite_is_admitted_without_changing_legacy_guard():
    from app.models.appeal_generation_service import _safe_rewrite
    assert not _safe_rewrite(ORIGINAL, REWRITE)
    assert validator.validate_rewrite(ORIGINAL, REWRITE).accepted


@pytest.mark.parametrize("original,rewrite", [
    ("Our community is standing beside families.", "Our community stands beside families."),
    ("Your contribution is reminding our neighbors.", "Your contribution reminds our neighbors."),
    ("Please donate water for 20 people in Malabe.", "Donate water for 20 people in Malabe."),
])
def test_local_inflections_and_grammar(original, rewrite):
    assert validator.validate_rewrite(original, rewrite).accepted


@pytest.mark.parametrize("original,rewrite", [
    ("Abandoned animals need essential veterinary medicine. The cost is rising.",
     "The cost is increasing. Abandoned animals require necessary veterinary medicine."),
    ("Your contribution can provide food for families.",
     "Your donation can provide food for families."),
    ("Shelters are completely full. Animals require food and warm blankets.",
     "Shelters are full. Animals need food and warm blankets."),
])
def test_bounded_paraphrases_preserve_original_claims(original, rewrite):
    assert validator.validate_rewrite(original, rewrite).accepted


@pytest.mark.parametrize("rewrite", [
    "Animals require necessary medicine and surgery.",
    "Children require necessary medicine.",
    "Animals require $100 for necessary medicine.",
    "Animals require necessary medicine tomorrow.",
    "Animals provide necessary medicine.",
])
def test_paraphrasing_does_not_admit_invented_details(rewrite):
    assert not validator.validate_rewrite("Animals need essential medicine.", rewrite).accepted


@pytest.mark.parametrize("original,rewrite,reason", [
    ("Donate water for 20 people.", "Donate water for 200 people.", "changed_quantity"),
    ("The goal changed by -20 percent.", "The goal changed by 20 percent.", "changed_quantity"),
    ("Provide 20% of supplies.", "Provide 20 of supplies.", "changed_quantity"),
    ("Provide up to 20 tents.", "Provide 20 tents.", "changed_quantity_qualifier"),
    ("Donate $20 for water.", "Donate $200 for water.", "changed_amount"),
    ("Donate $20 for water.", "Donate €20 for water.", "changed_amount"),
    ("Donate by January 20.", "Donate by January 21.", "changed_date"),
    ("Donate through https://example.test/a.", "Donate through https://example.test/b.", "changed_contact"),
    ("Donate through https://example.test/Pay.", "Donate through https://example.test/pay.", "changed_contact"),
    ("Contact help@example.test.", "Contact other@example.test.", "changed_contact"),
    ("Donate water in Malabe.", "Donate water in Colombo.", "changed_name"),
    ("Hope Foundation provides water.", "Hopes Foundation provides water.", "changed_name"),
    ("Please donate water.", "Please donate water tomorrow.", "changed_deadline_or_urgency"),
    ("We do not need tents.", "We do need tents.", "changed_negation"),
    ("We need food.", "We need food and medicine.", "unsupported_claim_or_changed_relationship"),
    ("We help families.", "We are a registered charity and help families.", "unsupported_claim_or_changed_relationship"),
    ("Alice gives food to Bob.", "Bob gives food to Alice.", "changed_name"),
    ("The family needs warm clothing.", "The family needed warm clothing.", "unsupported_claim_or_changed_relationship"),
    ("We were providing food.", "We provide food.", "unsupported_claim_or_changed_relationship"),
    ("We need 20 tents and 10 bottles.", "We need 10 tents and 20 bottles.", "unsupported_claim_or_changed_relationship"),
    # Clause-scoped negation now supplies a more precise diagnostic for the same rejection.
    ("We provide food, not tents.", "We provide tents, not food.", "changed_negation"),
    ("We may provide food.", "We will provide food.", "unsupported_claim_or_changed_relationship"),
    ("We only provide food.", "We provide food.", "unsupported_claim_or_changed_relationship"),
    ("When a crisis hits, families need food.", "A crisis hits. Families need food.", "unsupported_claim_or_changed_relationship"),
    ("When a crisis hits, families need food.", "Families need food.", "unsupported_claim_or_changed_relationship"),
    ("Donate water.", "  ", "empty_rewrite"),
])
def test_factual_changes_fail_closed(original, rewrite, reason):
    result = validator.validate_rewrite(original, rewrite)
    assert not result.accepted
    assert result.reason == reason


@pytest.mark.parametrize("text", ["මෙම පවුල් සඳහා උදව් කරන්න", "இந்த குடும்பங்களுக்கு உதவுங்கள்", "Families in Malabé need food."])
def test_non_latin_keeps_existing_validation(text):
    calls = []
    def fallback(original, rewrite):
        calls.append((original, rewrite))
        return original == rewrite
    assert validator.is_safe_rewrite(text, text, fallback=fallback)
    assert not validator.is_safe_rewrite(text, text + " new", fallback=fallback)
    assert len(calls) == 2


def test_diagnostic_logs_only_fixed_reason_not_appeal_content(caplog):
    with caplog.at_level(logging.INFO, logger=validator.__name__):
        assert not validator.is_safe_rewrite("We need water.", "We need medicine.", fallback=lambda *args: True)
    assert "unsupported_claim_or_changed_relationship" in caplog.text
    assert "medicine" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("original,rewrite", [
    (ORIGINAL, REWRITE), (SCHOLARSHIP, SCHOLARSHIP_REWRITE),
    ("Abandoned animals need essential medicine. The cost is rising.",
     "The cost is increasing. Abandoned animals require necessary medicine."),
])
async def test_repair_accepts_safe_paraphrase_with_one_provider_call(monkeypatch, tmp_path, original, rewrite):
    from app.models import appeal_generation_service as service
    from app.services import appeal_budget as budgets
    calls = []
    def score(confidence):
        return {"final_label": "high", "quality_score": 3.95, "raw_quality_score": 3.95,
                "confidence": confidence, "class_probs": {"high": confidence}}
    # Approved policy: acceptance requires a visible gain, not only classifier confidence.
    scores = iter([[{**score(.7), "quality_score": 3.9}], [{**score(.8), "quality_score": 4.0}]])
    monkeypatch.setattr(service.guide, "batch_score", lambda *args: next(scores))
    monkeypatch.setattr(service.guide, "guidance", lambda *args: {})
    monkeypatch.setattr(service, "REJECTION_LOG_PATH", tmp_path / "rejected.jsonl")
    async def provider(prompt, budget):
        assert validator.REWRITE_CONSTRAINTS in prompt
        assert "Paraphrase this donation appeal" in prompt
        calls.append(prompt)
        budget.consume()
        budget.account(True)
        return rewrite, "offline-provider"
    monkeypatch.setattr(service, "_call", provider)
    client = "safe-paraphrase-integration-test"
    day = budgets.improvement_day()
    prior = budgets.DAILY.pop((day, client), None)
    try:
        result = await service.repair(original, {"language": "English"}, client)
        assert result["kept"] and result["improved_appeal"] == rewrite
        assert result["rejection_reason"] is None
        assert len(calls) == result["gemini_calls_used"] == 1
        assert not service.REJECTION_LOG_PATH.exists()
    finally:
        budgets.DAILY.pop((day, client), None)
        if prior is not None:
            budgets.DAILY[(day, client)] = prior
