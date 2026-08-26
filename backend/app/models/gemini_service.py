import asyncio
import re

from app.models.config import settings
from app.models.quality_service import get_quality_score


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
2. CONTENT DEPTH: Develop the appeal fully - do not pad, but do not truncate.
   Underdeveloped appeals score medium regardless of other qualities.
3. CALL TO ACTION: Every appeal must contain an explicit, specific donation ask.
   Generic endings like "please help" score lower than "donate today to provide X".
4. CONCRETE IMPACT: State what the donation provides in specific terms drawn
   from the verified need. "Your donation provides clothing" scores higher than
   "your donation helps families".
5. NO REPETITION: Do not repeat the location name, campaign type, or any phrase
   more than once. Repetition is the top predictor of medium-quality scores.
6. TONE CONSISTENCY: Maintain one tone throughout. Mixing urgent and hopeful
   language within the same appeal reduces coherence scores.
7. STRICT GOAL BINDING: The campaign goal must be reflected verbatim in meaning.
   If the goal mentions children, the appeal must focus on children - not families,
   not the community in general. If the goal mentions wellbeing, the appeal must
   address wellbeing specifically - not infrastructure, not material goods unless
   stated in the verified need.
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


def _has_invented_person(text: str) -> bool:
    """Return True if the text contains hallucinated individuals or narrative drift."""
    return any(pattern.search(text) for pattern in _INVENTED_PERSON_PATTERNS)


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


async def call_gemini_with_key_fallback(prompt: str, temp: float) -> dict:
    for key_index, api_key in enumerate(_gemini_api_keys(), start=1):
        for attempt_temp in (temp, max(0.1, temp - 0.3)):
            try:
                appeal_text = await call_gemini_with_key(prompt, attempt_temp, api_key)
                appeal_text = appeal_text.strip()
                if not appeal_text:
                    break
                if not _has_invented_person(appeal_text):
                    return {
                        "model": settings.GEMINI_MODEL,
                        "temperature": attempt_temp,
                        "appeal_text": appeal_text,
                        "provider": f"gemini_key_{key_index}",
                    }
                print(
                    f"Hallucination detected (key={key_index}, temp={attempt_temp:.1f}) - "
                    f"{'retrying at lower temp' if attempt_temp == temp else 'skipping key'}."
                )
            except Exception as exc:
                print(f"Gemini key {key_index} failed (temp={attempt_temp}): {exc}")
                break
    return {}


def _build_fallback_appeal(form_data: dict) -> str:
    location      = form_data.get("location") or "our community"
    need          = form_data.get("verified_need") or "urgent support"
    goal          = form_data.get("campaign_goal") or "help those affected recover"
    campaign_type = (form_data.get("campaign_type") or "relief").replace("_", " ")
    if need.strip().lower() == "cloths":
        need = "clothes"

    return (
        f"Families in {location} need {need}. "
        f"This {campaign_type} campaign aims to {goal}. "
        "Our community is coming together to help. Please donate today."
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

    try:
        prompt = _build_generation_prompt(form_data)
        for key_index, api_key in enumerate(_gemini_api_keys(), start=1):
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
                if appeal_text and not _has_invented_person(appeal_text):
                    return appeal_text
                if appeal_text:
                    print("Invented person detected - using fallback.")
            except Exception as e:
                print(f"Gemini key {key_index} generation error: {e}")
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
