"""Local, conservative admission of grammatical rewrites; no models or network.

This supports inflections, bounded paraphrases, clause splitting/deletion and
grounded donation requests. Factual equivalence cannot be proved by lexical checks.
Unknown claims fail closed; existing non-Latin handling remains with the caller.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
import re
import unicodedata
from collections.abc import Callable

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_WORD = re.compile(r"[^\W\d_]+|\d+(?:[.,]\d+)*", re.UNICODE)
_GRAMMAR = frozenset("a an the and or but for to of in on at by with from into through as such whether that this these those is are was were be been being it its please".split())
_SCOPE = frozenset("not never no without if when unless can could may might must will would should only approximately estimated potentially allegedly".split())
_NEGATION = frozenset("not never no without".split())
_CONTACT = re.compile(r"https?://[^\s<>]+|[\w.+-]+@[\w.-]+\.[a-z]{2,}|\+\d[\d ()-]{6,}\d", re.I)
_MONEY = re.compile(r"(?:[$€£₹]|\b(?:USD|LKR|Rs\.?|EUR|GBP))\s*\d[\d,.]*|\b\d[\d,.]*\s*(?:dollars?|rupees?|USD|LKR|EUR|GBP)\b", re.I)
_DATE = re.compile(r"\b(?:\d{1,4}[-/]\d{1,2}[-/]\d{1,4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,?\s+\d{4})?)\b", re.I)
_QUALIFIED_QUANTITY = re.compile(r"\b(?:up to|at most|at least|less than|more than|about|approximately|around|under|over)\s+\d+(?:[.,]\d+)*", re.I)
_TIME_WORDS = frozenset("today tomorrow yesterday tonight immediately urgently urgent now daily weekly monthly annually".split())
_NAME = re.compile(r"\b(?:in|at|from|by|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})|\b((?:[A-Z][\w'-]+\s+){1,4}(?:Foundation|Charity|Trust|Hospital|School))\b")
_IRREGULAR = {"children": "child", "people": "person", "men": "man", "women": "woman"}
# Keep equivalents narrow: beneficiary types, items, promises and quantities
# must never become interchangeable. Anchors are checked before token matching.
_PARAPHRASE_GROUPS = (
    ("need", "needs", "needing", "require", "requires", "requiring"),
    ("donation", "donations", "contribution", "contributions"),
    ("essential", "necessary"),
    ("rising", "increasing"),
)
_PARAPHRASE_FORMS = {word: group[0] for group in _PARAPHRASE_GROUPS for word in group}
_CLAUSE_BREAK = re.compile(r"[.!?;,\u2014\u2013]+(?:\s|$)?|\b(?:but|yet)\b", re.I)
_REQUEST = re.compile(r"^\s*(?:please\s+)?(?:consider\s+)?(?:donat(?:e|ing)|support(?:ing)?|giv(?:e|ing)|contribut(?:e|ing))\b", re.I)
_PURPOSE = re.compile(r"^(.+?)\s+so(?:\s+that)?\s+they\s+(?:can|could|may)\s+(.+)$", re.I)
_STATED_GOAL = re.compile(r"\b(?:dreams?|hopes?|aims?|goals?)\s+(?:of|for|to|is(?:\s+to)?)\s+(.+?)(?=\s+(?:(?:simply\s+)?because|but|although|however|yet)\b|\s+and\s+(?:need|can|cannot|require|lack)\b|[.!?;]|$)", re.I)
_SUBJECT_END = re.compile(r"\b(?:from|in|at|with|who|whose|are|is|were|was|need|needs|can|cannot|could|may|will|would|dream|dreams|hope|hopes)\b", re.I)

REWRITE_CONSTRAINTS = (
    "Improve clarity, remove filler, and end with a clear donation request grounded in the original appeal. "
    "Keep the beneficiaries and donation purpose unchanged. Preserve negated meanings and conditional certainty: "
    "'can provide' must not become 'provides' or 'will provide'. You may split sentences or omit a complete statement, "
    "but never reverse its meaning. Do not add 'today', 'now', a deadline, an amount, or urgency absent from the original. "
    "Paraphrase for natural, concise wording and readable sentence structure, rather than adding details to chase a score. "
    "Keep each claim grounded in its original clause and preserve who does what for whom. "
    "You may reorder complete statements, split sentences, remove filler, and use natural equivalent wording. "
    "Preserve the beneficiaries, circumstances, donation purpose, quantities and degree of certainty. "
    "Do not invent people, personal stories, scenarios, outcomes, organizations, services or matching donations. "
    "Do not fill in missing information suggested by the rating, invent an amount, or strengthen promises. "
    "A request such as 'Please support these students' is allowed only when those beneficiaries are already stated. "
)


@dataclass(frozen=True)
class RewriteValidation:
    accepted: bool
    reason: str | None = None


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("’", "'")
    # In an explicit additive construction, 'not just X—but Y' asserts X.
    # Leave ordinary negation and incomplete 'not just X' statements intact.
    text = re.sub(r"\bnot\s+(?:just|only)\s+(?=[^.!?;]*(?:\bbut\b|[—–]))", "", text, flags=re.I)
    text = re.sub(r"\bcan't\b", "cannot", text, flags=re.I)
    text = re.sub(r"\bwon't\b", "will not", text, flags=re.I)
    text = re.sub(r"n't\b", " not", text, flags=re.I)
    return re.sub(r"\bcannot\b", "can not", text, flags=re.I)


def _forms(word: str) -> set[str]:
    """Bounded inflections, without stemming unrelated derivational words."""
    word = word.casefold()
    result = {word, _IRREGULAR.get(word, word)}
    if word in _PARAPHRASE_FORMS:
        result.add(_PARAPHRASE_FORMS[word])
    if len(word) > 4 and word.endswith("ies"):
        result.add(word[:-3] + "y")
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        result.add(word[:-1])
    if len(word) > 5 and word.endswith("es"):
        result.add(word[:-2])
    for suffix in ("ing",):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            base = word[:-len(suffix)]
            result.update((base, base + "e"))
            if len(base) > 3 and base[-1] == base[-2]:
                result.add(base[:-1])
    return result


def _tokens(text: str) -> list[str]:
    return [w.casefold() for w in _WORD.findall(text) if w.casefold() not in _GRAMMAR]


def _subsequence(candidate: list[str], source: list[str]) -> bool:
    position = 0
    for word in candidate:
        while position < len(source) and not (_forms(word) & _forms(source[position])):
            position += 1
        if position == len(source):
            return False
        position += 1
    return True


def _matches(pattern: re.Pattern, text: str) -> set[str]:
    # URL paths and email local parts can be case-sensitive: preserve contacts.
    return {re.sub(r"\s+", "", m.group() if pattern is _CONTACT else m.group().casefold()).rstrip(".,;!?") for m in pattern.finditer(text)}


def _clauses(text: str) -> list[tuple[str, set[str]]]:
    result = []
    for sentence in re.split(r"[.!?;]+(?:\s|$)", text):
        conditional = re.match(r"\s*(if|when|unless)\b", sentence, re.I)
        inherited = {conditional.group(1).casefold()} if conditional else set()
        for part in _CLAUSE_BREAK.split(sentence):
            # Each side of an affirmative causal statement can stand alone.
            # Do not detach a reason from a negated/modal/conditional assertion.
            causal = re.split(r"\b(?:simply\s+)?because\b", part, maxsplit=1, flags=re.I)
            parts = causal if len(causal) == 2 and not inherited and not set(_tokens(causal[0])) & _SCOPE else [part]
            result.extend((value.strip(), inherited) for value in parts if value.strip())
    return result


def _grounded_purpose_request(request_body: str, original: str) -> bool:
    """Admit an intended benefit, never a promise or a new factual assertion.

    The recipient and benefit must be linked in the same original sentence.
    An inability such as 'cannot afford tuition' can support an appeal to help
    afford tuition; it cannot support an assertion that tuition is now affordable.
    'Pursue' is admitted only with an explicitly stated aspiration's object.
    """
    match = _PURPOSE.fullmatch(request_body.strip())
    if not match:
        return False
    recipient, benefit = _tokens(match[1]), match[2].strip().rstrip(".")
    if not recipient or set(recipient) & _SCOPE:
        return False
    parts = re.split(r"\s+and\s+(?=pursue\b)", benefit, flags=re.I)
    for sentence in re.split(r"[.!?;]+(?:\s|$)", original):
        # Do not borrow an object or aspiration across a contrast introducing
        # another beneficiary or an explicitly unwanted donation purpose.
        sentence = re.split(r"\b(?:but|whereas|while)\b", sentence, maxsplit=1, flags=re.I)[0]
        source = _tokens(sentence)
        subject = _tokens(_SUBJECT_END.split(sentence, maxsplit=1)[0])
        if not _subsequence(recipient, subject):
            continue
        valid = True
        for part in parts:
            words = _tokens(part)
            if not words or set(words) & _SCOPE:
                valid = False
                break
            goal = re.fullmatch(r"pursue\s+(?:their\s+)?(.+)", part.strip(), re.I)
            if goal:
                target = _tokens(goal[1])
                valid = bool(target) and any(
                    not set(w.casefold() for w in _WORD.findall(sentence[:m.start()])[-3:]) & _NEGATION
                    and not set(_tokens(m[1])) & _NEGATION
                    and _subsequence(target, _tokens(m[1]))
                    for m in _STATED_GOAL.finditer(sentence))
            elif set(source) & _NEGATION:
                # Only financial inability is inverted within this intended-benefit
                # request. Other negative facts keep their original meaning.
                inability = re.search(r"\bcan\s+not\s+afford\s+(.+?)(?=[,.!?;]|$)", sentence, re.I)
                valid = len(words) > 1 and words[0] == "afford" and inability is not None and _subsequence(words[1:], _tokens(inability[1]))
            else:
                valid = _subsequence(words, source)
            if not valid:
                break
        if valid:
            return True
    return False


def validate_rewrite(original: str, rewrite: str, *, anchors_only: bool = False) -> RewriteValidation:
    """Return a fixed diagnostic code, never source text, keys, or provider data."""
    if not isinstance(original, str) or not isinstance(rewrite, str) or not rewrite.strip():
        return RewriteValidation(False, "empty_rewrite")
    original, rewrite = _normalise(original), _normalise(rewrite)
    if not anchors_only and any(c.isalpha() and ord(c) > 127 for c in original + rewrite):
        return RewriteValidation(False, "unsupported_language")
    for pattern, reason in ((_CONTACT, "changed_contact"), (_MONEY, "changed_amount"), (_DATE, "changed_date")):
        if _matches(pattern, original) != _matches(pattern, rewrite):
            return RewriteValidation(False, reason)
    numbers = lambda text: set(re.findall(r"(?<!\w)[+-]?\d+(?:[.,]\d+)*(?:\s*%)?", text))
    if numbers(original) != numbers(rewrite):
        return RewriteValidation(False, "changed_quantity")
    if _matches(_QUALIFIED_QUANTITY, original) != _matches(_QUALIFIED_QUANTITY, rewrite):
        return RewriteValidation(False, "changed_quantity_qualifier")
    names = lambda text: {m.group(1) or m.group(2) for m in _NAME.finditer(text)}
    if names(original) != names(rewrite):
        return RewriteValidation(False, "changed_name")
    before, after = _tokens(original), _tokens(rewrite)
    if not (set(after) & _TIME_WORDS) <= (set(before) & _TIME_WORDS):
        return RewriteValidation(False, "changed_deadline_or_urgency")
    if not (set(after) & _NEGATION) <= (set(before) & _NEGATION):
        return RewriteValidation(False, "changed_negation")
    if anchors_only:
        # Passing anchors is necessary, but semantic review must still check
        # beneficiaries, relationships, promises, negation and unsupported claims.
        return RewriteValidation(True)
    # Local clauses allow safe sentence splitting. Adjacent source windows retain
    # the subject of relative clauses; never pool vocabulary from the whole appeal.
    clauses = _clauses(original)
    sources = [(" ".join(part for part, _ in clauses[start:start + size]),
                set().union(*(context for _, context in clauses[start:start + size]))) for start in range(len(clauses))
               for size in range(1, min(3, len(clauses) - start) + 1)]
    sentences = [(_tokens(s), bool(re.search(r"\b(?:was|were|had|did)\b", s, re.I)), context) for s, context in sources]
    for sentence, context in _clauses(rewrite):
        content = _tokens(sentence)
        if not content:
            continue
        request = _REQUEST.match(sentence)
        if request:
            # Only an imperative, with an object grounded in the source. New
            # actions, purposes, recipients, amounts and dates remain forbidden.
            target = _tokens(sentence[request.end():])
            if target and not set(target) & _SCOPE and any(_subsequence(target, source) for source, _, _ in sentences):
                continue
            if _grounded_purpose_request(sentence[request.end():], original):
                continue
        past = bool(re.search(r"\b(?:was|were|had|did)\b", sentence, re.I))
        if not any(past == source_past and ((set(content) & _SCOPE) | context) == ((set(source) & _SCOPE) | source_context)
                   and _subsequence(content, source) for source, source_past, source_context in sentences):
            if any(past == source_past and _subsequence(content, source)
                   and set(content) & _NEGATION != set(source) & _NEGATION for source, source_past, _ in sentences):
                return RewriteValidation(False, "changed_negation")
            return RewriteValidation(False, "unsupported_claim_or_changed_relationship")
    return RewriteValidation(True)


def is_safe_rewrite(original: str, rewrite: str, *, fallback: Callable[[str, str], bool]) -> bool:
    result = validate_rewrite(original, rewrite)
    if result.reason == "unsupported_language":
        # No English inflection rules are imposed on Sinhala/Tamil or mixed text.
        return fallback(original, rewrite)
    if not result.accepted:
        logger.info("Appeal rewrite facts_guard detail=%s", result.reason)
    return result.accepted
