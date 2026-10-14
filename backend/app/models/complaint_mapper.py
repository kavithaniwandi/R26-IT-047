"""Map free-text complaint notes onto the severity model's complaint vocabulary."""
from __future__ import annotations

from functools import lru_cache
import json
import re
from pathlib import Path

from app.models.text_negation import is_span_negated, normalize_clinical_text, tokenize_with_boundaries


CLINICAL_COVERAGE_LEXICON_PATH = (
    Path(__file__).resolve().parents[2] / "ml_models" / "complaint_coverage_lexicon.json"
)
COMPLAINT_SYNONYMS_PATH = (
    Path(__file__).resolve().parents[2] / "ml_models" / "complaint_synonyms.json"
)
COMPLAINT_DANGER_TERMS_PATH = (
    Path(__file__).resolve().parents[2] / "ml_models" / "complaint_danger_terms.json"
)

COMPLAINT_COVERAGE_STOP_WORDS = {
    "a",
    "after",
    "and",
    "at",
    "complaint",
    "complaints",
    "denies",
    "for",
    "from",
    "in",
    "is",
    "no",
    "now",
    "of",
    "on",
    "patient",
    "presents",
    "request",
    "requesting",
    "reported",
    "review",
    "since",
    "stated",
    "symptom",
    "symptoms",
    "the",
    "this",
    "to",
    "today",
    "without",
    "with",
}


@lru_cache(maxsize=1)
def _clinical_coverage_exclusions() -> set[str]:
    data = json.loads(CLINICAL_COVERAGE_LEXICON_PATH.read_text(encoding="utf-8"))
    excluded = set()
    for values in data.values():
        excluded.update(str(value).lower() for value in values)
    return excluded


@lru_cache(maxsize=1)
def _synonym_groups() -> dict:
    return json.loads(COMPLAINT_SYNONYMS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _danger_config() -> dict:
    return json.loads(COMPLAINT_DANGER_TERMS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _danger_terms() -> list[str]:
    data = _danger_config()
    return [str(term).lower() for term in data.get("terms") or []]


@lru_cache(maxsize=1)
def _danger_co_occurrence_rules() -> list[dict]:
    data = _danger_config()
    return list(data.get("co_occurrence_rules") or [])


def _normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9_ ]", " ", str(text or "").lower().replace("|", " "))
    return re.sub(r"\s+", " ", text).strip()


def _word_pattern(pattern: str) -> re.Pattern:
    return re.compile(rf"(?<![a-z0-9_]){pattern}(?![a-z0-9_])")


def _negation_search_text(text: str) -> str:
    return normalize_clinical_text(str(text or "").replace("|", " "))


class ComplaintMapper:
    """Phrase mapper backed by the fitted complaint CountVectorizer vocabulary."""

    def __init__(self, vocabulary: dict[str, int] | list[str] | set[str]):
        terms = vocabulary.keys() if isinstance(vocabulary, dict) else vocabulary
        self.term_set = {_normalize(term) for term in terms if _normalize(term)}
        all_synonym_targets = set()
        for group_name, group in _synonym_groups().items():
            if group_name == "conditional":
                for conditional_group in group.values():
                    all_synonym_targets.update(conditional_group)
            else:
                all_synonym_targets.update(group)
        missing_targets = sorted(all_synonym_targets - self.term_set)
        if missing_targets:
            raise ValueError(f"Complaint synonym targets missing from model vocabulary: {missing_targets}")
        max_and_parts = [len(term.split(" and ")) for term in self.term_set]
        self.max_and_parts = max(max_and_parts) if max_and_parts else 1
        self.terms = sorted(self.term_set, key=lambda s: (-len(s), s))
        self._patterns = [(term, _word_pattern(re.escape(term))) for term in self.terms]
        self._synonym_patterns_by_group = self._build_synonym_patterns()
        self._danger_patterns = [(term, _word_pattern(re.escape(term))) for term in _danger_terms()]
        self._danger_co_occurrence_rules = [
            {
                "label": str(rule.get("label") or "danger co-occurrence"),
                "allergy_patterns": [
                    (str(term).lower(), _word_pattern(re.escape(str(term).lower())))
                    for term in rule.get("allergy_terms") or []
                ],
                "airway_patterns": [
                    (str(term).lower(), _word_pattern(re.escape(str(term).lower())))
                    for term in rule.get("airway_terms") or []
                ],
            }
            for rule in _danger_co_occurrence_rules()
        ]

    def _build_synonym_patterns(self) -> dict[str, list[tuple[str, re.Pattern]]]:
        groups = {}
        for group_name, group in _synonym_groups().items():
            if group_name == "conditional":
                for conditional_name, conditional_group in group.items():
                    groups[f"conditional:{conditional_name}"] = [
                        (target, _word_pattern(pattern))
                        for target, patterns in conditional_group.items()
                        for pattern in patterns
                    ]
            else:
                groups[group_name] = [
                    (target, _word_pattern(pattern))
                    for target, patterns in group.items()
                    for pattern in patterns
                ]
        return groups

    def _enabled_synonym_patterns(
        self,
        approved_synonyms: bool = False,
        conditional_synonyms: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> list[tuple[str, re.Pattern]]:
        patterns = list(self._synonym_patterns_by_group.get("base", []))
        if approved_synonyms:
            patterns.extend(self._synonym_patterns_by_group.get("approved", []))
        for name in conditional_synonyms or []:
            patterns.extend(self._synonym_patterns_by_group.get(f"conditional:{name}", []))
        return patterns

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

    def map(
        self,
        text: str,
        approved_synonyms: bool = False,
        conditional_synonyms: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> list[str]:
        delimited = self._map_delimited(text)

        cleaned = _negation_search_text(text)
        candidates = []
        for term in delimited:
            pattern = _word_pattern(re.escape(term))
            match = pattern.search(cleaned)
            if match and not is_span_negated(cleaned, match.start()):
                candidates.append((match.start(), match.end(), term, False))
        for term, pattern in self._enabled_synonym_patterns(approved_synonyms, conditional_synonyms):
            for match in pattern.finditer(cleaned):
                if is_span_negated(cleaned, match.start()):
                    continue
                candidates.append((match.start(), match.end(), term, True))
        for term, pattern in self._patterns:
            for match in pattern.finditer(cleaned):
                if is_span_negated(cleaned, match.start()):
                    continue
                candidates.append((match.start(), match.end(), term, False))

        matches = []
        occupied = []
        seen = set()
        for start, end, term, allow_overlap in sorted(candidates, key=lambda item: (item[0], -(item[1] - item[0]), item[2])):
            if term in seen:
                continue
            if not allow_overlap and any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            matches.append((start, term))
            if not allow_overlap:
                occupied.append((start, end))
            seen.add(term)
        return [term for _, term in sorted(matches)]

    def _covered_words(
        self,
        text: str,
        approved_synonyms: bool = False,
        conditional_synonyms: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> set[str]:
        cleaned = _negation_search_text(text)
        covered = set()
        for _, pattern in self._enabled_synonym_patterns(approved_synonyms, conditional_synonyms):
            for match in pattern.finditer(cleaned):
                if is_span_negated(cleaned, match.start()):
                    continue
                covered.update(match.group(0).split())
        return covered

    def _negated_words(
        self,
        text: str,
        approved_synonyms: bool = False,
        conditional_synonyms: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> set[str]:
        cleaned = _negation_search_text(text)
        negated = set()
        synonym_patterns = self._enabled_synonym_patterns(approved_synonyms, conditional_synonyms)
        for _, pattern in [*synonym_patterns, *self._patterns]:
            for match in pattern.finditer(cleaned):
                if is_span_negated(cleaned, match.start()):
                    negated.update(match.group(0).split())
        tokens = tokenize_with_boundaries(cleaned)
        for index, token in enumerate(tokens):
            if token.boundary:
                continue
            starts_negation = token.text in {"no", "not", "denies", "deny", "denied", "without"}
            starts_negative_for = (
                token.text == "negative"
                and index + 1 < len(tokens)
                and tokens[index + 1].text == "for"
            )
            if not starts_negation and not starts_negative_for:
                continue

            collected = 0
            start_index = index + (2 if starts_negative_for else 1)
            for next_token in tokens[start_index:]:
                if next_token.boundary or collected >= 3:
                    break
                negated.add(next_token.text)
                collected += 1
        return negated

    def _coverage_parts(
        self,
        text: str,
        mapped: list[str],
        mode: str = "legacy",
        approved_synonyms: bool = False,
        conditional_synonyms: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> tuple[list[str], set[str], float]:
        cleaned = _normalize(text)
        cleaned = re.sub(r"^patient complains of ", "", cleaned)
        if not cleaned:
            return [], set(), 0.0
        parts = [part.strip() for part in cleaned.split(" and ") if part.strip()]
        if len(parts) <= 1:
            tokens = cleaned.split()
        else:
            tokens = " ".join(parts).split()
        complaint_words = set(tokens)
        complaint_words -= COMPLAINT_COVERAGE_STOP_WORDS
        complaint_words -= self._negated_words(text, approved_synonyms, conditional_synonyms)
        if mode == "clinical":
            complaint_words -= _clinical_coverage_exclusions()
            complaint_words = {word for word in complaint_words if not word.isdigit()}
        mapped_words = set(" ".join(mapped).split())
        mapped_words.update(self._covered_words(text, approved_synonyms, conditional_synonyms))
        mapped_words -= COMPLAINT_COVERAGE_STOP_WORDS
        if not complaint_words:
            return tokens, complaint_words, 0.0
        return tokens, complaint_words, min(1.0, len(complaint_words & mapped_words) / len(complaint_words))

    def coverage(
        self,
        text: str,
        mapped: list[str] | None = None,
        mode: str = "legacy",
        approved_synonyms: bool = False,
        conditional_synonyms: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> float:
        """Estimate how much of the complaint-like text mapped to vocabulary."""
        mapped = self.map(text, approved_synonyms, conditional_synonyms) if mapped is None else mapped
        return self._coverage_parts(
            text,
            mapped,
            mode=mode,
            approved_synonyms=approved_synonyms,
            conditional_synonyms=conditional_synonyms,
        )[2]

    def diagnostic(
        self,
        text: str,
        mapped: list[str] | None = None,
        mode: str = "legacy",
        approved_synonyms: bool = False,
        conditional_synonyms: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> dict:
        """Return transparent complaint-mapping details without changing mapping."""
        mapped = self.map(text, approved_synonyms, conditional_synonyms) if mapped is None else mapped
        tokens, complaint_words, coverage = self._coverage_parts(
            text,
            mapped,
            mode=mode,
            approved_synonyms=approved_synonyms,
            conditional_synonyms=conditional_synonyms,
        )
        mapped_words = set(" ".join(mapped).split())
        mapped_words.update(self._covered_words(text, approved_synonyms, conditional_synonyms))
        mapped_words -= COMPLAINT_COVERAGE_STOP_WORDS
        unmapped_terms = [
            token
            for token in tokens
            if token in complaint_words and token not in mapped_words
        ]
        return {
            "normalized_tokens": tokens,
            "mapped_terms": list(mapped),
            "unmapped_terms": unmapped_terms,
            "coverage": coverage,
        }

    def danger_terms(self, text: str) -> list[str]:
        cleaned = _negation_search_text(text)
        hits = []
        for term, pattern in self._danger_patterns:
            for match in pattern.finditer(cleaned):
                if is_span_negated(cleaned, match.start()):
                    continue
                if term not in hits:
                    hits.append(term)
        for rule in self._danger_co_occurrence_rules:
            allergy_hit = self._first_active_match(cleaned, rule["allergy_patterns"])
            airway_hit = self._first_active_match(cleaned, rule["airway_patterns"])
            if allergy_hit and airway_hit:
                label = f"{rule['label']}: {allergy_hit} + {airway_hit}"
                if label not in hits:
                    hits.append(label)
        return hits

    @staticmethod
    def _first_active_match(cleaned: str, patterns: list[tuple[str, re.Pattern]]) -> str | None:
        for term, pattern in patterns:
            for match in pattern.finditer(cleaned):
                if not is_span_negated(cleaned, match.start()):
                    return term
        return None


def to_model_symptoms(
    mapper: ComplaintMapper,
    text: str,
    approved_synonyms: bool = False,
    conditional_synonyms: list[str] | tuple[str, ...] | set[str] | None = None,
) -> str:
    mapped = mapper.map(text, approved_synonyms, conditional_synonyms)
    return "|".join(mapped) if mapped else (text or "")
