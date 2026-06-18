"""Local handbook retrieval for university email replies."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from config import UNIVERSITY_HANDBOOK_PATH, VAULT_DIR


CATEGORY_KEYWORDS = {
    "course_registration": [
        "registration",
        "enroll",
        "enrollment",
        "course load",
        "credit hour",
        "add/drop",
        "add drop",
        "repeat course",
    ],
    "attendance": ["attendance", "short attendance", "75%", "sa grade", "eligible", "final examination"],
    "semester_freeze": ["semester freeze", "freeze", "unfreeze", "medical emergency", "rejoin"],
    "withdrawal": ["withdraw", "withdrawal", "drop course", "six weeks"],
    "credit_transfer": ["credit transfer", "cross campus", "program change", "transfer", "migration"],
    "examinations": ["exam", "examination", "midterm", "final", "make-up", "grading", "gpa", "cgpa"],
    "transcript_degree": ["transcript", "degree", "clearance", "convocation", "duplicate", "revised"],
    "fees_refund": ["fee", "fees", "payment", "refund", "dues", "installment"],
    "scholarship_financial_aid": ["scholarship", "financial aid", "discount", "need-based", "merit"],
    "discipline_conduct": ["discipline", "conduct", "harassment", "dress code", "id card", "violation"],
    "hostel_transport": ["hostel", "transport", "parking", "cafeteria"],
    "library_it": ["library", "lrc", "moodle", "wifi", "internet", "ipc", "login"],
    "grievance_counseling": ["grievance", "complaint", "counseling", "happiness center", "misconduct"],
}

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "because",
    "before",
    "being",
    "could",
    "email",
    "from",
    "have",
    "hello",
    "help",
    "into",
    "need",
    "please",
    "student",
    "that",
    "their",
    "there",
    "this",
    "want",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
}


@dataclass(frozen=True)
class HandbookSection:
    page: int
    text: str


def classify_university_email(text: str) -> str:
    text_lower = text.lower()
    scores = {
        category: sum(1 for keyword in keywords if keyword in text_lower)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general_inquiry"


@lru_cache(maxsize=1)
def load_handbook_sections() -> tuple[HandbookSection, ...]:
    candidates = [
        UNIVERSITY_HANDBOOK_PATH,
        VAULT_DIR / "docs" / "University_Handbook.md",
        VAULT_DIR / "docs" / "Company_Handbook.md",
    ]
    source = next((path for path in candidates if path.exists()), None)
    if source is None:
        return ()

    raw = source.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^## Page (\d+)\s*$", raw, re.MULTILINE))
    sections: list[HandbookSection] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        page_text = re.sub(r"\s+", " ", raw[start:end]).strip()
        if page_text:
            sections.append(HandbookSection(page=int(match.group(1)), text=page_text))
    return tuple(sections)


def _query_terms(query: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9%-]{2,}", query.lower())
        if term not in STOPWORDS
    }


def retrieve_handbook_context(query: str, limit: int = 4, max_chars: int = 2800) -> str:
    sections = load_handbook_sections()
    if not sections:
        return ""

    terms = _query_terms(query)
    category = classify_university_email(query)
    category_terms = set(CATEGORY_KEYWORDS.get(category, []))
    scored: list[tuple[int, HandbookSection]] = []

    for section in sections:
        haystack = section.text.lower()
        score = sum(3 for keyword in category_terms if keyword in haystack)
        score += sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, section))

    if not scored:
        return ""

    scored.sort(key=lambda item: item[0], reverse=True)
    snippets = []
    total_chars = 0
    for _score, section in scored[:limit]:
        snippet = section.text[:900].strip()
        addition = f"[Handbook page {section.page}] {snippet}"
        if total_chars + len(addition) > max_chars:
            break
        snippets.append(addition)
        total_chars += len(addition)

    return "\n\n".join(snippets)
