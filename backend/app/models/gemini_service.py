import asyncio
import re
import time

from app.models.config import settings
from app.models.quality_service import get_quality_score
from app.services.credit_monitor import mark_exhausted, record_failure, record_success

_PERMANENT_QUOTA_KEYWORDS = (
    "daily",
    "quota_exceeded",
    "billing",
    "resource_exhausted",
    "exceeded your current quota",
)
_TEMPORARY_RATE_KEYWORDS = (
    "429",
    "rate",
    "too many requests",
    "per_minute",
    "rpm",
)
_INVALID_MODEL_KEYWORDS = (
    "404",
    "not_found",
    "no longer available",
    "deprecated",
)


SYSTEM_INSTRUCTION = (
    "You are a factual donation-appeal copywriter. "
    "Convert the provided input data into appeal copy. "
    "RULES - all are mandatory:\n"
    "1. Use ONLY the facts given in the input data. Add nothing.\n"
    "2. Refer to beneficiaries only as groups explicitly supported by the input data. "
    "Use generic groups like 'families', 'households', 'individuals', or 'the community' unless "
    "the input names a specific group such as children, elderly people, or women. "
    "Never use a specific person's name, age, or backstory unless it appears verbatim in the input.\n"
    "3. Style guidelines are secondary. If any guideline implies inventing a person or scenario, ignore it.\n"
    "4. Never describe beneficiaries' emotions or mental states.\n"
    "5. Rules apply equally in English, Sinhala, and Tamil.\n"
    "6. Output ONLY the appeal text. No preamble, no sign-off."
)

CHANNEL_RULES = {
    "facebook": "Format for Facebook. 2-3 short paragraphs. Maximum 120 words. End with a direct call to action.",
    "website": "Format for a campaign page. 3 paragraphs: situation, what donations provide, call to action. 180-240 words.",
    "email": "Format for a donor email. 3-4 paragraphs building toward the ask. Close with a clear call to action. 150-220 words.",
    "sms": "Format for SMS. Maximum 160 characters. One sentence only.",
    "whatsapp": "Format for WhatsApp. Very short lines. Maximum 80 words. End with a direct ask.",
    "direct": "Conversational one-to-one tone. 3-4 sentences. Personal and warm. End with a specific, direct ask.",
}

_CHANNEL_RULES_DEFAULT = "Write 3-4 sentences with a direct call to action at the end."

TONE_GUIDANCE = {
    "hopeful":           "Use words like recover, rebuild, together, and community. Frame around what becomes possible with support.",
    "urgent":            "Convey urgency through the verified need facts. Keep it grounded and direct.",
    "compassionate":     "Use warm language about the affected community. Focus on dignity and collective support.",
    "trust":             "Use clear, factual language. Reference verified need and concrete impact.",
    "trustworthy":       "Use clear, factual language. Reference verified need and concrete impact.",
    "community":         "Write as a community member. Use 'our community', 'together', 'support each other'.",
    "community_focused": "Write as a community member. Use 'our community', 'together', 'support each other'.",
    "direct":            "State the situation and need plainly. Short sentences. End with a clear action verb.",
}

_TONE_GUIDANCE_DEFAULT = "Write with warmth and directness. Use community-centred language."

LENGTH_GUIDANCE = {
    "very_short":           "Write 1 sentence. State the location, need, and ask.",
    "very short":           "Write 1 sentence. State the location, need, and ask.",
    "short":                "Write 2-3 sentences, 60-90 words.",
    "short_1_2_sentences":  "Write 2-3 sentences, 60-90 words.",
    "medium":               "Write 3-4 sentences, 100-150 words.",
    "medium_3_4_sentences": "Write 3-4 sentences, 100-150 words.",
    "long":                 "Write 5+ sentences, 180-250 words.",
    "long_5_sentences":     "Write 5+ sentences, 180-250 words.",
}

_LENGTH_GUIDANCE_DEFAULT = "Write 3-5 sentences with a direct call to action."

# Quality constraints derived from the ML model's learned high-score features.
ML_QUALITY_CONSTRAINTS = """
QUALITY CONSTRAINTS (derived from appeal quality model - mandatory):
1. SENTENCE STRUCTURE: Write complete sentences averaging 10-14 words.
   Short fragments lower the quality score significantly.
2. CONTENT DEPTH: Develop the appeal using the input data only.
   Do NOT pad with generic community language to reach length.
   Every sentence must add new information. If it restates what was already
   said, cut it.
3. CALL TO ACTION: Every appeal must contain an explicit, specific donation ask.
   Generic endings like "please help" score lower than "donate today to provide X".
4. CONCRETE IMPACT: State what the donation provides in specific terms drawn
   from the verified need. "Your donation provides clothing" scores higher than
   "your donation helps families".
5. NO FILLER: Never use sentences like these. They contribute zero quality signal
   and the scoring model penalises them heavily:
   - "Collective action ensures..."
   - "Broad participation strengthens..."
   - "Organized response efforts allow..."
   - "Every contribution aligns with..."
   - "Together we can make a difference..."
   If you find yourself writing a sentence with no factual content from the
   input data, delete it.
6. NO REPETITION: Do not repeat the location name, campaign type, or any phrase
   more than once.
7. TONE CONSISTENCY: Maintain one tone throughout.
8. STRICT GOAL BINDING: If the goal mentions children, the appeal must focus
   on children. If it mentions wellbeing, address wellbeing specifically.
9. QUALITY OVER LENGTH: A focused 80-word appeal scores higher than a padded
   150-word appeal. Only expand length if you have genuine content to add.
"""

VARIANT_STYLES = [
    {
        "style_name": "formal",
        "style_instruction": (
            "Formal, factual tone. "
            "Lead with the verified need as a factual statement. "
            "Build toward the donation ask with evidence-based framing. "
            "Close with a specific, action-oriented CTA."
        ),
    },
    {
        "style_name": "community",
        "style_instruction": (
            "Warm, community-focused tone. "
            "Use 'our community', 'together', 'we stand with'. "
            "Frame the donation as collective action, not charity. "
            "Close with an inclusive CTA that emphasises shared responsibility."
        ),
    },
    {
        "style_name": "urgent",
        "style_instruction": (
            "Urgent but dignified tone. "
            "Open with the most pressing fact from the verified need. "
            "Use short, direct sentences - no more than 12 words each. "
            "Every sentence must move toward the donation ask. "
            "Close with a time-sensitive CTA."
        ),
    },
]

GENERATION_PROMPT = """\
TASK: Write a donation appeal using ONLY the facts in INPUT DATA below.

STYLE GUIDELINES (secondary - never override system rules):
- Language : {language}
- Channel  : {channel} - {channel_rules}
- Length   : {length_guidance}
- Tone     : {tone} - {tone_guidance}
- Style    : {style_instruction}

{ml_quality_constraints}

INPUT DATA (sole source of truth - do not add, invent, or assume anything):
- Location      : {location}
- Campaign type : {campaign_type}
- Verified need : {verified_need}
- Campaign goal : {campaign_goal}

BINDING CHECK - before writing, confirm:
- Who does this campaign serve? Use exactly that group throughout.
- What is the verified need? Mention it explicitly at least once.
- What is the campaign goal? The appeal must reflect this goal directly.

REMINDER: Beneficiaries = "families", "households", "individuals", or
"the community" only - UNLESS the campaign goal specifies a group like
"children", "elderly", or "women", in which case use that specific group.
Output the appeal in {language}. Nothing else."""


def _get_gemini_client(api_key: str | None = None):
    api_key = api_key or settings.GEMINI_API_KEY
    if not api_key:
        return None
    from google import genai
    return genai.Client(api_key=api_key)


def _gemini_api_keys() -> list[str]:
    return [
        key
        for key in (
            settings.GEMINI_API_KEY,
            settings.GEMINI_API_KEY2,
            settings.GEMINI_API_KEY3,
            settings.GEMINI_API_KEY4,
            settings.GEMINI_API_KEY5,
            settings.GEMINI_API_KEY6,
            settings.GEMINI_API_KEY7,
            settings.GEMINI_API_KEY8,
            settings.GEMINI_API_KEY9,
            settings.GEMINI_API_KEY10,
            settings.GEMINI_API_KEY11,
        )
        if key
    ]


def _normalise_key(value: str) -> str:
    return (
        value.lower().strip()
        .replace(" ", "_").replace("-", "_")
        .replace("(", "").replace(")", "")
        .replace("+", "").replace("/", "_")
    )


def _build_generation_prompt(form_data: dict, style: dict | None = None) -> str:
    campaign_type   = form_data.get("campaign_type") or ""
    channel         = form_data.get("channel") or ""
    tone            = form_data.get("tone") or ""
    length_category = form_data.get("length_category") or ""
    location        = form_data.get("location") or "the affected area"
    verified_need   = form_data.get("verified_need") or "urgent support"
    campaign_goal   = form_data.get("campaign_goal") or "help those affected recover"
    language        = form_data.get("language") or "English"

    if verified_need.strip().lower() == "cloths":
        verified_need = "clothes"

    length_key      = _normalise_key(length_category)
    length_guidance = LENGTH_GUIDANCE.get(length_key)
    if not length_guidance:
        for key, guidance in LENGTH_GUIDANCE.items():
            if length_key.startswith(key.split("_")[0]):
                length_guidance = guidance
                break

    active_style = style or VARIANT_STYLES[0]

    return GENERATION_PROMPT.format(
        campaign_type=campaign_type,
        location=location,
        verified_need=verified_need,
        campaign_goal=campaign_goal,
        language=language,
        tone=tone,
        tone_guidance=TONE_GUIDANCE.get(_normalise_key(tone), _TONE_GUIDANCE_DEFAULT),
        channel=channel,
        channel_rules=CHANNEL_RULES.get(_normalise_key(channel), _CHANNEL_RULES_DEFAULT),
        length_guidance=length_guidance or _LENGTH_GUIDANCE_DEFAULT,
        style_instruction=active_style["style_instruction"],
        ml_quality_constraints=ML_QUALITY_CONSTRAINTS,
    )


_INVENTED_PERSON_PATTERNS = [
    re.compile(
        r"\b[A-Z][a-z]{2,}\b(?=\s+and\s+(?:her|his|their)"
        r"|\s+(?:cradled|held|clutched|wept|cried|sobbed|fled|trembled))",
        re.UNICODE,
    ),
    re.compile(r"\b(?:young|little|small|tiny)\s+[A-Z][a-z]+\b", re.IGNORECASE | re.UNICODE),
    re.compile(
        r"\b[A-Z][a-z]{2,}'s\s+(?:family|children|child|son|daughter|home|husband|wife|mother|father)\b",
        re.UNICODE,
    ),
    re.compile(r"\b(?:her|his)\s+(?:children|child|family|home|husband|wife|son|daughter)\b", re.IGNORECASE),
    re.compile(r"\b\d+[-\s]year[-\s]old\b", re.IGNORECASE),
    re.compile(r"\b(?:a|one)\s+(?:mother|father|woman|man|child|farmer|fisherman|family)\b", re.IGNORECASE),
    re.compile(r"\b(?:she|he)\s+(?:wept|cried|sobbed|trembled|shook|whispered|fled|lost)\b", re.IGNORECASE),
    re.compile(r"නාමල්ගේ\s+පවුල|කුඩා\s+පුතා|පුංචි\s+දරුවා|අපගේ\s+පුංචි|තරුණ\s+මවක්", re.UNICODE),
    re.compile(r"சிறிய\s+\S+|இளம்\s+\S+", re.UNICODE),
]


_FILLER_PATTERNS = [
    re.compile(
        r"\b(collective action ensures|broad participation|organized response efforts|"
        r"every contribution aligns|together we can make)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(strengthens the overall region|move forward step by step|"
        r"throughout this important initiative)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(primary goal of this campaign|aligned with the campaign|"
        r"in line with our mission)\b",
        re.IGNORECASE,
    ),
]
_FILLER_THRESHOLD = 2

_INVENTED_SPECIFIC_PATTERNS = [
    re.compile(r"(?:\$|rs\.?|lkr)\s*\d+(?:[,.]\d+)?", re.IGNORECASE),
    re.compile(r"\b\d+\s*(?:day|week|month|year|hour)s?\s+supply\b", re.IGNORECASE),
    re.compile(r"\b\d+[-\s](?:day|week|month|year|hour)\b", re.IGNORECASE),
    re.compile(r"\b(?:hundreds|thousands|millions)\s+of\s+(?:families|people|households|children)\b", re.IGNORECASE),
    re.compile(r"\b(?:tarpaulin|blankets?|mattresses?|mosquito nets?)\b", re.IGNORECASE),
]


def _has_hallucination(text: str) -> tuple[bool, str]:
    """Return True with a reason when generated text drifts from factual copy."""
    for pattern in _INVENTED_PERSON_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"invented_person: {match.group()!r}"

    for pattern in _INVENTED_SPECIFIC_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"invented_specific: {match.group()!r}"

    filler_hits = []
    for pattern in _FILLER_PATTERNS:
        match = pattern.search(text)
        if match:
            filler_hits.append(match.group())

    if len(filler_hits) >= _FILLER_THRESHOLD:
        return True, f"generic_filler: {filler_hits}"

    return False, ""


def _has_invented_person(text: str) -> bool:
    """Return True if the text contains hallucinated individuals or narrative drift."""
    has_problem, _reason = _has_hallucination(text)
    return has_problem


def _detect_script(text: str) -> str:
    """Detect the dominant script from Unicode ranges."""
    sinhala_chars = sum(1 for char in text if "\u0D80" <= char <= "\u0DFF")
    tamil_chars = sum(1 for char in text if "\u0B80" <= char <= "\u0BFF")
    latin_chars = sum(1 for char in text if char.isascii() and char.isalpha())
    total = max(len(text), 1)

    if sinhala_chars / total > 0.1:
        return "Sinhala"
    if tamil_chars / total > 0.1:
        return "Tamil"
    if latin_chars / total > 0.3:
        return "English"
    return "unknown"


def _language_matches(text: str, expected_language: str) -> bool:
    """Return True when generated text matches the requested language."""
    detected = _detect_script(text)
    if expected_language == "English" and detected == "English":
        return True
    if expected_language == "Sinhala" and detected == "Sinhala":
        return True
    if expected_language == "Tamil" and detected == "Tamil":
        return True
    if detected == "unknown":
        return True
    return False


def score_text(text: str, language: str = "English") -> dict:
    """
    Delegate entirely to quality_service: single inference pipeline,
    no duplicate artifact loading.
    """
    result = get_quality_score(text, language)
    return {
        "quality_label": result["status"],
        "quality_score": result["score"],
        "confidence": result["confidence"],
        "confidence_normalised": result["confidence_normalised"],
        "confidence_display": result["confidence_display"],
    }


async def call_gemini_with_key(prompt: str, temp: float, api_key: str | None) -> str:
    def _generate() -> str:
        client = _get_gemini_client(api_key)
        if client is None:
            return ""
        from google.genai.types import GenerateContentConfig
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=GenerateContentConfig(
                temperature=temp,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )
        return response.text.strip() if response.text else ""
    return await asyncio.to_thread(_generate)


async def call_gemini(prompt: str, temp: float) -> str:
    return await call_gemini_with_key(prompt, temp, settings.GEMINI_API_KEY)


def _call_hf_llama_sync_with_temp(prompt: str, temperature: float) -> str:
    """
    Llama 3.2 3B via featherless-ai provider on HuggingFace.
    Uses HF_API_KEY; generated text is still validated before being returned.
    """
    from huggingface_hub import InferenceClient

    client = InferenceClient(
        token=settings.HF_API_KEY,
        provider="featherless-ai",
    )
    response = client.chat_completion(
        model="meta-llama/Llama-3.2-3B-Instruct",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=512,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _call_hf_llama_sync(prompt: str) -> str:
    return _call_hf_llama_sync_with_temp(prompt, 0.3)


async def call_gemini_with_key_fallback(
    prompt: str,
    temp: float,
    *,
    language: str = "English",
    max_retries: int = 2,
) -> dict:
    from app.services.credit_monitor import _key_state

    gemini_keys = list(enumerate(_gemini_api_keys(), start=1))
    gemini_all_failed = True
    invalid_model_detected = False

    for key_index, api_key in gemini_keys:
        label = f"gemini_key_{key_index}"
        if _key_state.get(label, {}).get("exhausted", False):
            print(f"Skipping {label} - marked exhausted")
            continue
        retry_temp = temp
        for attempt in range(1, max_retries + 1):
            try:
                appeal_text = await call_gemini_with_key(prompt, retry_temp, api_key)
                appeal_text = appeal_text.strip()
                if not appeal_text:
                    break
                has_problem, reason = _has_hallucination(appeal_text)
                if not has_problem:
                    record_success(label)
                    gemini_all_failed = False
                    return {
                        "model": settings.GEMINI_MODEL,
                        "temperature": retry_temp,
                        "appeal_text": appeal_text,
                        "provider": label,
                    }
                print(
                    f"Hallucination (key={key_index}, attempt={attempt}, "
                    f"temp={retry_temp:.1f}): {reason}"
                )
                retry_temp = max(0.1, retry_temp - 0.2)
            except Exception as exc:
                print(f"GEMINI KEY {key_index} FULL ERROR: {type(exc).__name__}: {exc}")
                error_str = str(exc).lower()
                if any(kw in error_str for kw in _INVALID_MODEL_KEYWORDS):
                    print("CRITICAL: Gemini model string is invalid - check GEMINI_MODEL in .env")
                    invalid_model_detected = True
                elif any(kw in error_str for kw in _PERMANENT_QUOTA_KEYWORDS):
                    print(f"Gemini key {key_index} daily quota exhausted - marked permanently")
                    mark_exhausted(label)
                elif any(kw in error_str for kw in _TEMPORARY_RATE_KEYWORDS):
                    print(f"Gemini key {key_index} rate limited - waiting 10s before next key")
                    await asyncio.sleep(10)
                    record_failure(label, "rate_limited_temporary")
                else:
                    print(f"Gemini key {key_index} failed: {exc}")
                    record_failure(label, str(exc))
                break
        if invalid_model_detected:
            break

    if gemini_all_failed and not invalid_model_detected:
        for key_index, _api_key in gemini_keys:
            label = f"gemini_key_{key_index}"
            if not settings.HF_API_KEY:
                mark_exhausted(label)
                continue
            if not getattr(settings, "HF_API_KEY", None):
                mark_exhausted(label)
                continue

            if _key_state.get(label, {}).get("calls", 0) == 0:
                print(f"{label} had no successful calls recorded in this run")

    if settings.HF_API_KEY:
        if language in ("Sinhala", "Tamil"):
            print(
                f"HF Llama skipped for {language} - model cannot reliably generate "
                f"non-Latin scripts. Using template fallback."
            )
            return {}

        print("All Gemini keys exhausted - trying HuggingFace Llama fallback...")
        _HF_LABEL = "huggingface-featherless"

        for hf_attempt, hf_temp in enumerate((0.3, 0.2, 0.1), start=1):
            try:
                appeal_text = await asyncio.to_thread(
                    _call_hf_llama_sync_with_temp,
                    prompt,
                    hf_temp,
                )
                appeal_text = appeal_text.strip()
                if not appeal_text:
                    continue
                if not _language_matches(appeal_text, language):
                    print(
                        f"HF Llama wrong language detected "
                        f"(expected={language}, attempt={hf_attempt}) - rejecting"
                    )
                    continue

                has_problem, reason = _has_hallucination(appeal_text)
                if not has_problem:
                    print(f"HF Llama succeeded on attempt {hf_attempt}")
                    record_success(_HF_LABEL)
                    return {
                        "model": "llama-3.2-3b-instruct",
                        "temperature": hf_temp,
                        "appeal_text": appeal_text,
                        "provider": _HF_LABEL,
                    }

                print(
                    f"HF Llama hallucination detected "
                    f"(attempt={hf_attempt}, temp={hf_temp}): {reason}"
                )
            except Exception as exc:
                error_str = str(exc).lower()
                if any(kw in error_str for kw in _PERMANENT_QUOTA_KEYWORDS):
                    print(f"HF Llama quota exhausted: {exc}")
                    mark_exhausted(_HF_LABEL)
                elif any(kw in error_str for kw in _TEMPORARY_RATE_KEYWORDS):
                    print(f"HF Llama rate limited - waiting 10s before giving up on fallback")
                    await asyncio.sleep(10)
                    record_failure(_HF_LABEL, "rate_limited_temporary")
                else:
                    print(f"HF Llama attempt {hf_attempt} failed: {exc}")
                    record_failure(_HF_LABEL, str(exc))
                break

        print("HF Llama fallback exhausted or all attempts hallucinated.")

    return {}


def _build_fallback_appeal(form_data: dict) -> str:
    fallback_templates = {
        "Sinhala": (
            "{location} ප්‍රදේශයේ පවුල් වලට {need} අවශ්‍ය වේ. "
            "මෙම {campaign_type} ව්‍යාපාරය {goal} අරමුණු කරයි. "
            "අපේ ප්‍රජාව එකට ඉදිරියට යමු. අදම පරිත්‍යාග කරන්න."
        ),
        "Tamil": (
            "{location} பகுதியில் உள்ள குடும்பங்களுக்கு {need} தேவைப்படுகிறது. "
            "இந்த {campaign_type} பிரச்சாரம் {goal} நோக்கமாக கொண்டுள்ளது. "
            "நம் சமூகம் ஒன்றாக முன்னேறுவோம். இன்றே நன்கொடை வழங்குங்கள்."
        ),
        "English": (
            "Families in {location} urgently need {need}. "
            "This {campaign_type} campaign aims to {goal}. "
            "Our community is coming together to help. Please donate today."
        ),
    }
    location      = form_data.get("location") or "our community"
    need          = form_data.get("verified_need") or "urgent support"
    goal          = form_data.get("campaign_goal") or "help those affected recover"
    campaign_type = (form_data.get("campaign_type") or "relief").replace("_", " ")
    language      = form_data.get("language") or "English"
    if need.strip().lower() == "cloths":
        need = "clothes"

    template = fallback_templates.get(language, fallback_templates["English"])
    return template.format(
        location=location,
        need=need,
        goal=goal,
        campaign_type=campaign_type,
    )


def _build_fallback_variant(form_data: dict) -> dict:
    appeal_text = _build_fallback_appeal(form_data)
    scoring = score_text(appeal_text, language=form_data.get("language", "English"))
    return {
        "model": "fallback_template",
        "temperature": 0.0,
        "style": "fallback",
        "appeal_text": appeal_text,
        "quality_label": scoring["quality_label"],
        "quality_score": scoring["quality_score"],
        "confidence": scoring["confidence"],
        "confidence_normalised": scoring["confidence_normalised"],
        "confidence_display": scoring["confidence_display"],
    }


REQUIRED_GENERATION_FIELDS = {
    "location": "Location",
    "verified_need": "Verified Need",
    "campaign_goal": "Campaign Goal",
}


def _missing_required_generation_fields(form_data: dict) -> list[str]:
    return [
        label
        for field, label in REQUIRED_GENERATION_FIELDS.items()
        if not (form_data.get(field) or "").strip()
    ]


def _ensure_required_generation_fields(form_data: dict) -> None:
    missing_fields = _missing_required_generation_fields(form_data)
    if missing_fields:
        raise ValueError(f"Please fill in: {', '.join(missing_fields)}")


def generate_donation_appeal(form_data: dict) -> str:
    _ensure_required_generation_fields(form_data)
    language = form_data.get("language", "English")
    from app.services.credit_monitor import _key_state
    invalid_model_detected = False

    try:
        prompt = _build_generation_prompt(form_data)
        for key_index, api_key in enumerate(_gemini_api_keys(), start=1):
            label = f"gemini_key_{key_index}"
            if _key_state.get(label, {}).get("exhausted", False):
                print(f"Skipping {label} - marked exhausted")
                continue
            client = _get_gemini_client(api_key)
            if client is None:
                continue
            from google.genai.types import GenerateContentConfig
            try:
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=GenerateContentConfig(
                        temperature=0.3,
                        system_instruction=SYSTEM_INSTRUCTION,
                    ),
                )
                appeal_text = response.text.strip()
                if appeal_text:
                    has_problem, reason = _has_hallucination(appeal_text)
                    if not has_problem:
                        record_success(label)
                        print(f"Recording success for {label}")
                        return appeal_text
                    print(f"Generated appeal rejected ({reason}) - using fallback.")
            except Exception as e:
                error_str = str(e).lower()
                if any(kw in error_str for kw in _INVALID_MODEL_KEYWORDS):
                    print("CRITICAL: Gemini model string is invalid - check GEMINI_MODEL in .env")
                    invalid_model_detected = True
                elif any(kw in error_str for kw in _PERMANENT_QUOTA_KEYWORDS):
                    print(f"Gemini key {key_index} daily quota exhausted - marked permanently")
                    mark_exhausted(label)
                elif any(kw in error_str for kw in _TEMPORARY_RATE_KEYWORDS):
                    print(f"Gemini key {key_index} rate limited - waiting 10s before next key")
                    record_failure(label, "rate_limited_temporary")
                    time.sleep(10)
                else:
                    record_failure(label, str(e))
                print(f"Gemini key {key_index} generation error: {e}")
                if invalid_model_detected:
                    break

        if invalid_model_detected:
            return _build_fallback_appeal(form_data)

        if settings.HF_API_KEY and language == "English":
            for hf_temp in (0.3, 0.2, 0.1):
                try:
                    appeal_text = _call_hf_llama_sync_with_temp(prompt, hf_temp).strip()
                    if not appeal_text:
                        continue
                    if not _language_matches(appeal_text, language):
                        print(
                            f"HF single generation wrong language detected "
                            f"(expected={language}, temp={hf_temp}) - rejecting"
                        )
                        continue
                    has_problem, reason = _has_hallucination(appeal_text)
                    if not has_problem:
                        record_success("huggingface-featherless")
                        return appeal_text
                    print(
                        f"HF single generation rejected ({reason}) "
                        f"(temp={hf_temp}) - retrying."
                    )
                except Exception as e:
                    error_str = str(e).lower()
                    if any(kw in error_str for kw in _PERMANENT_QUOTA_KEYWORDS):
                        mark_exhausted("huggingface-featherless")
                    elif any(kw in error_str for kw in _TEMPORARY_RATE_KEYWORDS):
                        record_failure("huggingface-featherless", "rate_limited_temporary")
                    else:
                        record_failure("huggingface-featherless", str(e))
                    print(f"HF single generation failed: {e}")
                    break
        elif settings.HF_API_KEY and language in ("Sinhala", "Tamil"):
            print(
                f"HF Llama skipped for {language} - model cannot reliably generate "
                f"non-Latin scripts. Using template fallback."
            )
    except Exception as e:
        print(f"Gemini generation error: {e}")
    return _build_fallback_appeal(form_data)


async def generate_appeal_variants(campaign_data: dict, top_n: int = 3) -> list[dict]:
    _ensure_required_generation_fields(campaign_data)

    language = campaign_data.get("language", "English")
    styles = VARIANT_STYLES[:top_n]
    tasks = [
        call_gemini_with_key_fallback(
            _build_generation_prompt(campaign_data, style=style),
            temp=0.5,
            language=language,
        )
        for style in styles
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    candidates: list[dict] = []
    seen_texts: set[str] = set()

    for index, result in enumerate(results):
        if isinstance(result, Exception) or not result:
            print(f"Style variant {index + 1} failed: {result}")
            continue

        appeal_text = result.get("appeal_text", "").strip()
        if not appeal_text:
            continue

        normalised = re.sub(r"\s+", " ", appeal_text.lower())
        if normalised in seen_texts:
            continue
        seen_texts.add(normalised)

        scoring = score_text(appeal_text, language=language)
        candidates.append({
            "model": result["model"],
            "temperature": 0.5,
            "style": styles[index]["style_name"],
            "appeal_text": appeal_text,
            "quality_label": scoring["quality_label"],
            "quality_score": scoring["quality_score"],
            "confidence": scoring["confidence"],
            "confidence_normalised": scoring["confidence_normalised"],
            "confidence_display": scoring["confidence_display"],
        })

    candidates.sort(key=lambda item: item["quality_score"], reverse=True)
    if not candidates:
        return [_build_fallback_variant(campaign_data)]
    return candidates[:top_n]


def _diagnose_weaknesses(appeal_text: str, language: str = "English") -> list[dict]:
    text = (appeal_text or "").strip()
    words = re.findall(r"\S+", text)
    sentences = [s.strip() for s in re.split(r"[.!?।།]+", text) if s.strip()]
    lower_text = text.lower()

    issues: list[dict] = []

    word_count = len(words)
    if word_count < 35:
        issues.append({
            "dimension": "Content depth",
            "severity": "high",
            "issue": "The appeal is too short to explain the need, impact, and donation action clearly.",
            "value": f"{word_count} words",
            "target": "At least 60 words for most channels",
        })
    elif word_count < 60:
        issues.append({
            "dimension": "Content depth",
            "severity": "medium",
            "issue": "The appeal may need a little more detail about what donors will help provide.",
            "value": f"{word_count} words",
            "target": "60-120 words for concise campaign copy",
        })

    donate_terms = (
        "donate", "donation", "give", "support", "contribute", "fund",
        "help provide", "please help", "please support"
    )
    if not any(term in lower_text for term in donate_terms):
        issues.append({
            "dimension": "Call to action",
            "severity": "high",
            "issue": "The appeal does not include a clear donor action.",
            "value": "No explicit ask found",
            "target": "Use a direct request such as donate, support, or contribute",
        })

    impact_terms = (
        "food", "water", "medicine", "medical", "shelter", "clothes", "supplies",
        "hygiene", "families", "households", "children", "elderly"
    )
    if not any(term in lower_text for term in impact_terms):
        issues.append({
            "dimension": "Concrete impact",
            "severity": "medium",
            "issue": "The appeal does not clearly state what support will provide.",
            "value": "Impact terms not detected",
            "target": "Name the supplies, service, or beneficiary group",
        })

    if sentences:
        avg_sentence_len = word_count / len(sentences)
        if avg_sentence_len > 24:
            issues.append({
                "dimension": "Readability",
                "severity": "medium",
                "issue": "Sentences are long, which can make the appeal harder to scan.",
                "value": f"{avg_sentence_len:.1f} words per sentence",
                "target": "10-18 words per sentence",
            })
        elif avg_sentence_len < 6 and word_count >= 20:
            issues.append({
                "dimension": "Sentence structure",
                "severity": "low",
                "issue": "The appeal uses very short fragments and may read less complete.",
                "value": f"{avg_sentence_len:.1f} words per sentence",
                "target": "Complete sentences averaging 10-14 words",
            })

    repeated_words = [
        word
        for word in set(re.findall(r"\b[a-zA-Z]{5,}\b", lower_text))
        if lower_text.count(word) >= 4
    ]
    if repeated_words:
        issues.append({
            "dimension": "Repetition",
            "severity": "low",
            "issue": "Some terms appear repeatedly and may reduce perceived quality.",
            "value": ", ".join(repeated_words[:3]),
            "target": "Avoid repeating key phrases more than needed",
        })

    if not issues:
        issues.append({
            "dimension": "Overall structure",
            "severity": "low",
            "issue": "No major quality issue was detected. A final human review is still recommended.",
            "value": "Stable",
            "target": "Keep the appeal factual, specific, and action-oriented",
        })

    return issues


def _build_improvement_prompt(appeal_text: str, language: str, issues: list[dict]) -> str:
    issue_lines = "\n".join(
        f"- {item['issue']} Target: {item['target']}"
        for item in issues
    )
    word_count = len(appeal_text.split())
    min_words = max(120, word_count * 2)
    return f"""\
TASK: Write a substantially better version of the appeal below.

ORIGINAL APPEAL ({word_count} words):
{appeal_text}

PROBLEMS TO FIX:
{issue_lines}

STRICT REQUIREMENTS FOR THE NEW VERSION:
1. Must be at least {min_words} words. The original is too short.
2. Do not reuse or rearrange sentences from the original. Write fresh.
3. Open with a specific situation statement using the location and need when present.
4. Include a concrete impact statement: exactly what will donations provide?
5. Include one community or human element: who is affected and how.
6. End with a strong, specific call to action, not just "donate today".
7. No invented names, ages, statistics, dates, or details not in the original.
8. Write entirely in {language}.

Output ONLY the improved appeal. Nothing else.
"""


def _fallback_improved_appeal(appeal_text: str) -> str:
    text = re.sub(r"\s+", " ", (appeal_text or "").strip())
    if not text:
        return ""
    if re.search(r"\b(donate|support|contribute|give)\b", text, re.IGNORECASE):
        return text
    return f"{text} Please donate today to provide verified support where it is needed most."


def _is_weak_improvement(original_text: str, improved_text: str) -> bool:
    original_words = original_text.split()
    improved_words = improved_text.split()
    min_words = max(120, len(original_words) * 2)

    if len(improved_words) < min_words:
        return True

    original_sentences = {
        re.sub(r"\s+", " ", sentence.strip().lower())
        for sentence in re.split(r"[.!?]+", original_text)
        if len(sentence.split()) >= 4
    }
    improved_lower = re.sub(r"\s+", " ", improved_text.lower())
    reused_sentences = sum(
        1
        for sentence in original_sentences
        if sentence and sentence in improved_lower
    )

    return reused_sentences > 0


async def improve_appeal_text(appeal_text: str, language: str = "English") -> dict:
    original = score_text(appeal_text, language)
    issues = _diagnose_weaknesses(appeal_text, language)
    prompt = _build_improvement_prompt(appeal_text, language, issues)

    result = {}
    improved_text = ""

    async def _generate_improvement_with_retry() -> tuple[dict, str]:
        result = await call_gemini_with_key_fallback(prompt, temp=0.35, language=language)
        improved_text = (result.get("appeal_text") or "").strip() if result else ""
        if improved_text and _is_weak_improvement(appeal_text, improved_text):
            retry_prompt = (
                f"{prompt}\n\n"
                "The previous rewrite was too short or too similar. Rewrite again with "
                "new sentence structure, richer factual explanation, and the required "
                "minimum word count. Do not copy original sentences."
            )
            result = await call_gemini_with_key_fallback(retry_prompt, temp=0.45, language=language)
            improved_text = (result.get("appeal_text") or "").strip() if result else ""
        return result or {}, improved_text

    try:
        result, improved_text = await asyncio.wait_for(
            _generate_improvement_with_retry(),
            timeout=15.0,
        )
    except asyncio.TimeoutError:
        print("Improvement generation timed out - using fallback")

    if not improved_text:
        improved_text = _fallback_improved_appeal(appeal_text)

    improved = score_text(improved_text, language)
    return {
        "original_score": original["quality_score"],
        "original_label": original["quality_label"],
        "original_confidence": original["confidence"],
        "issues": issues,
        "improved_appeal": improved_text,
        "improved_score": improved["quality_score"],
        "improved_label": improved["quality_label"],
        "improved_confidence": improved["confidence"],
        "method": result.get("model", "fallback_template") if result else "fallback_template",
    }
