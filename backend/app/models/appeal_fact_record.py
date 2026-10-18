"""Source-backed editing context, extracted locally without inferring new facts.

Mention tags are navigation aids, not independently verified assertions. Every
source statement is retained, including languages or entities not recognized by
the lightweight patterns. Reviewers still validate the proposed rewrite.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re


@dataclass(frozen=True)
class Evidence:
    text: str
    start: int
    end: int
    statement_id: int


@dataclass
class FactRecord:
    schema_version: int = 1
    source_statements: list[Evidence] = field(default_factory=list)
    beneficiary_mentions: list[Evidence] = field(default_factory=list)
    location_mentions: list[Evidence] = field(default_factory=list)
    need_statements: list[Evidence] = field(default_factory=list)
    donation_purpose_statements: list[Evidence] = field(default_factory=list)
    donation_requests: list[Evidence] = field(default_factory=list)
    quantity_mentions: list[Evidence] = field(default_factory=list)
    amount_mentions: list[Evidence] = field(default_factory=list)
    date_mentions: list[Evidence] = field(default_factory=list)
    urgency_mentions: list[Evidence] = field(default_factory=list)
    contact_mentions: list[Evidence] = field(default_factory=list)
    qualification_statements: list[Evidence] = field(default_factory=list)


_STATEMENT = re.compile(
    r"\S.*?(?:(?<!\bRs)(?<!\bDr)(?<!\bMr)(?<!\bMs)(?<!\bMrs)[.!?](?=\s|$)|$)", re.S | re.I)
_BENEFICIARY = re.compile(
    r"\b(?:families|family|households?|students?|children|patients?|animals?|pets?|"
    r"residents?|people|communities|refugees?|survivors?)\b", re.I)
_LOCATION = re.compile(
    r"(?i:\b(?:in|at|from|near|across)\s+)"
    r"(?P<location>[A-Z][^\W\d_]*(?:[ \t]+[A-Z][^\W\d_]*){0,3})")
_NEED = re.compile(r"\b(?:need\w*|requir\w*|necessities|lack\w*|cannot\s+afford|can't\s+afford)\b", re.I)
_PURPOSE = re.compile(r"\b(?:fund\w*|donat\w*|contribut\w*|support\w*|provid\w*|give|giving)\b", re.I)
_REQUEST = re.compile(r"(?:^|[.!?]\s+)\s*(?:please\s+)?(?:consider\s+)?(?:donate|give|support|contribute)\b", re.I)
_QUANTITY = re.compile(
    r"(?<!\w)[+-]?\d+(?:[.,]\d+)*(?:\s*%)?|\b(?:hundreds?|thousands?|millions?)\b", re.I)
_AMOUNT = re.compile(
    r"(?:[$€£₹]|\b(?:USD|LKR|Rs\.?|EUR|GBP))\s*\d[\d,.]*|"
    r"\b\d[\d,.]*\s*(?:dollars?|rupees?|USD|LKR|EUR|GBP)\b", re.I)
_DATE = re.compile(
    r"\b(?:\d{1,4}[-/]\d{1,2}[-/]\d{1,4}|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}(?:,?\s+\d{4})?)\b", re.I)
_URGENCY = re.compile(r"\b(?:today|tomorrow|tonight|now|urgent\w*|immediate\w*|emergency)\b", re.I)
_CONTACT = re.compile(r"https?://[^\s<>]+|[\w.+-]+@[\w.-]+\.[a-z]{2,}|\+\d[\d ()-]{6,}\d", re.I)
_QUALIFICATION = re.compile(
    r"\b(?:not|never|no|without|if|unless|when|only|cannot|can't|can|could|may|might|"
    r"approximately|estimated|up\s+to|at\s+least|at\s+most)\b", re.I)


def build_fact_record(text: str) -> dict:
    """Return JSON-compatible context with exact offsets into the original text.

    Empty fields mean no mention was extracted, not that the fact is false or
    safe to invent. Full statements are the authority for context and meaning.
    """
    record = FactRecord()
    for statement_id, match in enumerate(_STATEMENT.finditer(text), 1):
        statement = Evidence(match.group(), match.start(), match.end(), statement_id)
        record.source_statements.append(statement)
        for pattern, target in ((_NEED, record.need_statements),
                                (_PURPOSE, record.donation_purpose_statements),
                                (_REQUEST, record.donation_requests),
                                (_QUALIFICATION, record.qualification_statements)):
            if pattern.search(statement.text):
                target.append(statement)
        for pattern, target in ((_BENEFICIARY, record.beneficiary_mentions),
                                (_LOCATION, record.location_mentions),
                                (_QUANTITY, record.quantity_mentions),
                                (_AMOUNT, record.amount_mentions),
                                (_DATE, record.date_mentions),
                                (_URGENCY, record.urgency_mentions),
                                (_CONTACT, record.contact_mentions)):
            for mention in pattern.finditer(statement.text):
                start, end = mention.span("location") if pattern is _LOCATION else mention.span()
                if pattern is _CONTACT:
                    end = start + len(statement.text[start:end].rstrip(".,;!?"))
                target.append(Evidence(statement.text[start:end], statement.start + start,
                                       statement.start + end, statement_id))
    return asdict(record)
