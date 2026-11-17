"""
Citizen Accessibility evaluation module for CDTM dimension e.

Evaluates structural proxies for citizen comprehension:
  - English sentence complexity, Flesch Reading Ease & Flesch-Kincaid Grade Level.
  - Hindi structural indicators (sentence length, word length). English formulas are NEVER applied to Hindi.
  - Contextual detection of unexplained acronyms (e.g. DBT, UT, KCC) and administrative terms (e.g. Aadhaar).
  - Actionability indicators for practical citizen use.

CRITICAL INVARIANTS:
1. Automated metrics are structural proxies only, NOT proof of citizen comprehension.
2. Actual Citizen Accessibility remains strictly 'not_evaluated' until supported
   by empirical citizen studies.
3. Aadhaar is an administrative term requiring contextual explanation, not an acronym.
"""
import re
from typing import Any, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pure-Python English Syllable & Readability Helpers
# ---------------------------------------------------------------------------

def _count_syllables_english(word: str) -> int:
    """Heuristic syllable counter for English words (pure Python, stdlib only)."""
    clean = re.sub(r"[^a-z]", "", word.lower())
    if not clean:
        return 1
    if len(clean) <= 3:
        return 1

    # Remove trailing silent e (unless ends with -le and preceding consonant)
    if clean.endswith("e") and not clean.endswith("le"):
        clean = clean[:-1]

    # Count vowel groups
    vowel_runs = re.findall(r"[aeiouy]+", clean)
    count = len(vowel_runs)

    # Common suffixes
    if clean.endswith("ed") and not clean.endswith("ted") and not clean.endswith("ded"):
        count = max(1, count - 1)

    return max(1, count)


def compute_english_readability(text: str) -> tuple[float, float, str]:
    """
    Compute Flesch Reading Ease and Flesch-Kincaid Grade Level for English text.
    Returns: (flesch_reading_ease, flesch_kincaid_grade, category_label)
    """
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    num_sentences = max(1, len(sentences))

    words = re.findall(r"\b[A-Za-z0-9_-]+\b", text)
    num_words = max(1, len(words))

    num_syllables = sum(_count_syllables_english(w) for w in words)

    # Standard formulas
    asl = num_words / num_sentences  # Average Sentence Length
    asw = num_syllables / num_words  # Average Syllables per Word

    fre = 206.835 - (1.015 * asl) - (84.6 * asw)
    fre = round(max(0.0, min(100.0, fre)), 2)

    fkgl = 0.39 * asl + 11.8 * asw - 15.59
    fkgl = round(max(0.0, fkgl), 2)

    if fre >= 80:
        cat = "Easy / Conversational"
    elif fre >= 60:
        cat = "Standard / Plain English"
    elif fre >= 40:
        cat = "Moderately Difficult / Formal"
    elif fre >= 20:
        cat = "Difficult / Academic"
    else:
        cat = "Very Difficult / Legal Jargon"

    return fre, fkgl, cat


# ---------------------------------------------------------------------------
# Unexplained Acronym & Administrative Jargon Checker
# ---------------------------------------------------------------------------

KNOWN_ACRONYMS = {
    "DBT": ["direct benefit transfer", "direct bank transfer", "प्रत्यक्ष लाभ अंतरण"],
    "UT": ["union territory", "केंद्र शासित प्रदेश"],
    "KCC": ["kisan credit card", "किसान क्रेडिट कार्ड"],
    "CSC": ["common service centre", "कॉमन सर्विस सेंटर"],
    "NIC": ["national informatics centre"],
    "UIDAI": ["unique identification authority of india"],
    "MSP": ["minimum support price", "न्यूनतम समर्थन मूल्य"],
}

ADMIN_TERMS = {
    "Aadhaar": ["12-digit", "national id", "identity", "आधार कार्ड", "12 अंकों"],
}


def find_unexplained_terms(text: str) -> tuple[list[str], list[str]]:
    """
    Check if bureaucratic acronyms or administrative terms appear without
    inline explanatory context (in brackets, parentheses, or adjacent text).
    """
    unexplained_acronyms: list[str] = []
    unexplained_admin_terms: list[str] = []

    text_lower = text.lower()

    # 1. Check acronyms
    for acronym, expansions in KNOWN_ACRONYMS.items():
        pattern = r"\b" + re.escape(acronym) + r"\b"
        matches = list(re.finditer(pattern, text))
        if matches:
            # Check if any expansion appears anywhere in the surrounding text or inline
            has_expansion = any(exp in text_lower for exp in expansions)
            if not has_expansion:
                unexplained_acronyms.append(acronym)

    # 2. Check administrative terms (e.g. Aadhaar — not an acronym, but needs contextual explanation)
    for term, explanations in ADMIN_TERMS.items():
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            # Check if accompanied by explanatory context
            has_context = any(exp in text_lower for exp in explanations)
            # Also check if followed by bracketed explanation e.g. "Aadhaar [your ID]"
            bracket_match = re.search(r"Aadhaar\s*\[[^\]]+\]", text, re.IGNORECASE)
            if not has_context and not bracket_match:
                unexplained_admin_terms.append(f"{term} (lacks plain-language contextual description)")

    return unexplained_acronyms, unexplained_admin_terms


def detect_actionability(text: str) -> tuple[bool, list[str]]:
    """Check for practical citizen guidance (action verbs, steps, deadlines, contact)."""
    indicators: list[str] = []
    text_lower = text.lower()

    patterns = [
        (r"\b(apply|submit|register|visit|download|upload|contact|call|approach)\b", "Contains clear action verbs"),
        (r"\b(portal|website|office|helpline|counter|csc)\b", "Specifies practical channel or location"),
        (r"\b(deadline|before|last date|within \d+ days|till)\b", "States explicit deadline or timeframe"),
        (r"\b(documents required|bring your|carry|along with)\b", "Lists required citizen documentation"),
    ]

    for pat, desc in patterns:
        if re.search(pat, text_lower):
            indicators.append(desc)

    return len(indicators) > 0, indicators


# ---------------------------------------------------------------------------
# Result Schemas
# ---------------------------------------------------------------------------

class AccessibilityProxyMetrics(BaseModel):
    """Structural and lexical proxy metrics for accessibility."""

    language: Literal["en", "hi"]
    sentence_count: int
    word_count: int
    avg_sentence_length: float
    flesch_reading_ease: float | None = None
    flesch_kincaid_grade: float | None = None
    readability_category: str
    unexplained_acronyms: list[str] = Field(default_factory=list)
    unexplained_administrative_terms: list[str] = Field(default_factory=list)
    actionable_guidance_present: bool = False
    actionable_indicators: list[str] = Field(default_factory=list)


class CitizenAccessibilityResult(BaseModel):
    """
    Evaluation result for CDTM Dimension e: Citizen Accessibility.

    IMPORTANT: Actual Citizen Accessibility strictly remains 'not_evaluated'
    until validated by empirical citizen comprehension studies. The enclosed
    metrics are automated structural proxies only.
    """

    status: Literal["not_evaluated"] = Field(
        default="not_evaluated",
        description="Strictly not_evaluated pending empirical user studies.",
    )
    proxy_metrics: AccessibilityProxyMetrics
    structural_barrier_flagged: bool = Field(
        default=False,
        description="True if reading ease is low or unexplained acronyms/terms were detected.",
    )
    note: str = Field(
        default=(
            "CDTM Dimension e: Citizen Accessibility remains strictly not_evaluated until validated "
            "by empirical citizen comprehension studies. Automated readability scores and jargon checks "
            "are structural proxy metrics, not verified measures of citizen comprehension."
        ),
        description="Mandatory methodological limitation disclaimer.",
    )
    controlled_demo: bool = Field(
        default=False,
        description="True when evaluated under controlled demonstration mode.",
    )


def evaluate_accessibility(
    text: str,
    language: str = "en",
    demo: bool = False,
) -> CitizenAccessibilityResult:
    """
    Evaluate structural accessibility proxies for English or Hindi text.
    Never marks the dimensional status verified.
    """
    clean = text.strip()
    lang = "hi" if language.lower() in ("hi", "hindi") else "en"

    # Split sentences
    sentences = [s.strip() for s in re.split(r"[.!?।]+", clean) if s.strip()]
    sentence_count = max(1, len(sentences))
    words = re.findall(r"\b[\w-]+\b", clean)
    word_count = max(1, len(words))
    asl = round(word_count / sentence_count, 2)

    unexplained_acronyms, unexplained_terms = find_unexplained_terms(clean)
    has_action, action_indicators = detect_actionability(clean)

    if lang == "en":
        fre, fkgl, cat = compute_english_readability(clean)
        barrier = fre < 50.0 or len(unexplained_acronyms) > 0 or len(unexplained_terms) > 0
    else:
        # Hindi: structural indicators only; NEVER apply English Flesch formulas
        fre = None
        fkgl = None
        if asl > 25:
            cat = "Complex Syntax (High sentence length)"
        elif asl > 15:
            cat = "Standard Administrative Hindi"
        else:
            cat = "Direct / Short Sentences"
        barrier = asl > 25 or len(unexplained_acronyms) > 0 or len(unexplained_terms) > 0

    proxy_metrics = AccessibilityProxyMetrics(
        language=lang,
        sentence_count=sentence_count,
        word_count=word_count,
        avg_sentence_length=asl,
        flesch_reading_ease=fre,
        flesch_kincaid_grade=fkgl,
        readability_category=cat,
        unexplained_acronyms=unexplained_acronyms,
        unexplained_administrative_terms=unexplained_terms,
        actionable_guidance_present=has_action,
        actionable_indicators=action_indicators,
    )

    return CitizenAccessibilityResult(
        status="not_evaluated",
        proxy_metrics=proxy_metrics,
        structural_barrier_flagged=barrier,
        controlled_demo=demo,
    )
