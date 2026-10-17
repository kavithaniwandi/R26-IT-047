from __future__ import annotations

import re
from dataclasses import dataclass


NEGATION_TOKENS = {"no", "not", "denies", "deny", "denied", "without"}
BOUNDARY_RE = re.compile(r"[.;,!?]")
TOKEN_RE = re.compile(r"[a-z0-9_]+|[.;,!?]", re.IGNORECASE)


@dataclass(frozen=True)
class TextToken:
    text: str
    start: int
    end: int
    boundary: bool = False


def normalize_clinical_text(text: str | None) -> str:
    cleaned = (text or "").lower()
    cleaned = re.sub(r"[^a-z0-9_.,;!?]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def tokenize_with_boundaries(text: str | None) -> list[TextToken]:
    normalized = normalize_clinical_text(text)
    tokens: list[TextToken] = []
    for match in TOKEN_RE.finditer(normalized):
        value = match.group(0)
        tokens.append(
            TextToken(
                text=value,
                start=match.start(),
                end=match.end(),
                boundary=bool(BOUNDARY_RE.fullmatch(value)),
            )
        )
    return tokens


def is_span_negated(text: str | None, start: int, window: int = 3) -> bool:
    tokens = tokenize_with_boundaries(text)
    before: list[TextToken] = []
    for token in tokens:
        if token.start >= start:
            break
        before.append(token)

    since_boundary: list[TextToken] = []
    for token in reversed(before):
        if token.boundary:
            break
        since_boundary.append(token)

    words = [token.text for token in reversed(since_boundary) if not token.boundary]
    nearby = words[-window:]
    if any(word in NEGATION_TOKENS for word in nearby):
        return True

    if len(nearby) >= 2:
        pairs = zip(nearby, nearby[1:])
        return any(first == "negative" and second == "for" for first, second in pairs)

    return False
