"""Map free-text complaint notes onto the severity model's complaint vocabulary."""
from __future__ import annotations

import re


def _normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9_ ]", " ", str(text or "").lower().replace("|", " "))
    return re.sub(r"\s+", " ", text).strip()


class ComplaintMapper:
    """Phrase mapper backed by the fitted complaint CountVectorizer vocabulary."""

    def __init__(self, vocabulary: dict[str, int] | list[str] | set[str]):
        terms = vocabulary.keys() if isinstance(vocabulary, dict) else vocabulary
        self.term_set = {_normalize(term) for term in terms if _normalize(term)}
        max_and_parts = [len(term.split(" and ")) for term in self.term_set]
        self.max_and_parts = max(max_and_parts) if max_and_parts else 1
        self.terms = sorted(self.term_set, key=lambda s: (-len(s), s))
        self._patterns = [(term, re.compile(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])")) for term in self.terms]

    def _map_delimited(self, text: str) -> list[str]:
        cleaned = _normalize(text)
        has_prompt_prefix = cleaned.startswith("patient complains of ")
        cleaned = re.sub(r"^patient complains of ", "", cleaned)
        if not cleaned:
            return []
        if cleaned in self.term_set:
            return [cleaned]

        parts = [part.strip() for part in cleaned.split(" and ") if part.strip()]
        if len(parts) <= 1:
            return []

        mapped = []
        i = 0
        while i < len(parts):
            best = None
            max_j = min(len(parts), i + self.max_and_parts)
            for j in range(max_j, i, -1):
                candidate = " and ".join(parts[i:j])
                if candidate in self.term_set:
                    best = (candidate, j)
                    break
            if best is None:
                i += 1
            else:
                mapped.append(best[0])
                i = best[1]
        return mapped

    def map(self, text: str) -> list[str]:
        delimited = self._map_delimited(text)
        if delimited:
            return delimited

        cleaned = _normalize(text)
        candidates = []
        for term, pattern in self._patterns:
            for match in pattern.finditer(cleaned):
                candidates.append((match.start(), match.end(), term))

        matches = []
        occupied = []
        seen = set()
        for start, end, term in sorted(candidates, key=lambda item: (item[0], -(item[1] - item[0]), item[2])):
            if term in seen:
                continue
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            matches.append((start, term))
            occupied.append((start, end))
            seen.add(term)
        return [term for _, term in sorted(matches)]

    def coverage(self, text: str, mapped: list[str] | None = None) -> float:
        """Estimate how much of the complaint-like text mapped to vocabulary."""
        mapped = self.map(text) if mapped is None else mapped
        cleaned = _normalize(text)
        cleaned = re.sub(r"^patient complains of ", "", cleaned)
        if not cleaned:
            return 0.0
        parts = [part.strip() for part in cleaned.split(" and ") if part.strip()]
        if len(parts) <= 1:
            complaint_words = set(cleaned.split())
        else:
            complaint_words = set(" ".join(parts).split())
        mapped_words = set(" ".join(mapped).split())
        if not complaint_words:
            return 0.0
        return min(1.0, len(complaint_words & mapped_words) / len(complaint_words))


def to_model_symptoms(mapper: ComplaintMapper, text: str) -> str:
    mapped = mapper.map(text)
    return "|".join(mapped) if mapped else (text or "")
