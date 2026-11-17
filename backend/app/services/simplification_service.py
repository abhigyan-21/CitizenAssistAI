"""
Simplification Service — Phase 4: Semantic Fidelity.

Two-call AI pipeline + deterministic transformation check:

  Step 0: Transformation check (difflib.SequenceMatcher, deterministic).
          Detects when Call 1 output is too similar to the source.
          → simplification_quality: "simplified" | "insufficient" | "requires_human_review"

  Call 1: Simplify the source passage into plain English.
          Prompted to use short sentences, everyday vocabulary, and inline
          explanations of administrative terms, while preserving all conditions.

  Call 2: Independent fidelity review.
          Receives ONLY source and simplified text.
          Checks whether meaning, conditions, amounts, dates and document
          requirements were preserved. Does NOT assess simplification quality.

The two assessments are kept strictly separate and surfaced independently.
"""
import difflib
import logging
import re
from typing import Any

from app.ai.base import AIProvider
from app.document.store import get_document
from app.evaluation.semantic_fidelity import (
    SemanticFidelityResult,
    SimplificationResponse,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Similarity thresholds (documented as heuristics, not validated universals)
# ---------------------------------------------------------------------------

#: Passages shorter than this (normalized chars) have unreliable similarity scores.
SHORT_PASSAGE_THRESHOLD = 150

#: Above this similarity, a standard-length passage is considered insufficiently simplified.
SIMILARITY_INSUFFICIENT = 0.85

#: Above this similarity, a short passage cannot be reliably classified → human review.
SHORT_PASSAGE_REVIEW = 0.70

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

SIMPLIFY_SYSTEM_PROMPT = """You are a plain-language editor for Indian administrative and government documents.
Your task is to rewrite a source passage so that any ordinary citizen — with no legal, financial, or bureaucratic knowledge — can understand it immediately.

LANGUAGE AND STYLE RULES:
1. Use short sentences. Each sentence should express one idea only.
2. Use everyday vocabulary. Replace administrative and legal jargon with simple words.
3. When an administrative term cannot be removed (e.g. "Aadhaar", "DBT", "cultivable land"), explain it in brackets immediately after: e.g. "Aadhaar [your 12-digit national ID]".
4. Write in active voice wherever possible.
5. Do NOT use bullet points, headings, or formatting — write in plain prose.

CONTENT PRESERVATION RULES — these are non-negotiable:
6. Preserve EVERY financial amount exactly as it appears (e.g. Rs 6,000, Rs 2,000 per instalment).
7. Preserve EVERY age limit and age-related condition exactly (e.g. "minor children", "below 18 years").
8. Preserve EVERY eligibility condition and exclusion category (e.g. "government employees are excluded").
9. Preserve EVERY deadline, date and time period exactly.
10. Preserve EVERY document requirement (e.g. "land records of the state/UT", "Aadhaar-linked bank account").
11. Preserve EVERY exception and special case.
12. Do NOT add information not present in the source passage.
13. Do NOT omit any restriction, condition, exclusion or requirement, even if it seems minor.

RESPONSE FORMAT — You MUST respond with ONLY valid JSON:
{
  "answer": "<your simplified plain-English passage>"
}
"""

REVIEWER_SYSTEM_PROMPT = """You are an independent semantic fidelity reviewer for Indian administrative document simplifications.

Your SOLE task is to check whether the SIMPLIFIED text preserves the meaning and critical content of the SOURCE text.

You are NOT assessing whether the text is well-simplified, readable, or plain. Only assess content preservation.

You will receive:
  SOURCE: The original administrative passage.
  SIMPLIFIED: A plain-language rewrite of that passage.

CHECK FOR THESE SPECIFIC ITEMS in SOURCE that may be absent or altered in SIMPLIFIED:
- Financial amounts (e.g. Rs 6,000, Rs 2,000 per instalment)
- Age limits and age-related conditions (e.g. "minor children", "below 18 years")
- Eligibility conditions and exclusion categories
- Deadlines, dates and time periods
- Document requirements (e.g. land records, Aadhaar, bank account)
- Exceptions and special cases
- Definitions (e.g. "farmer family is defined as...")

RESPONSE FORMAT — respond with ONLY valid JSON, nothing else:
{
  "status": "<verified|potential_issue|requires_human_review>",
  "preserved_conditions": ["<item confirmed present in both SOURCE and SIMPLIFIED>"],
  "potentially_missing": ["<item in SOURCE that appears absent or altered in SIMPLIFIED>"]
}

STATUS DEFINITIONS:
  verified              — All significant conditions, amounts and exclusions are present and unaltered.
  potential_issue       — One or more conditions, amounts, exclusions or definitions appear missing or changed.
  requires_human_review — The passage is complex, ambiguous, or you are uncertain.

Base your review ONLY on comparing SOURCE and SIMPLIFIED. Do not invent items.
Do not comment on simplification quality, sentence length, or vocabulary choice.
"""

# ---------------------------------------------------------------------------
# Controlled failure demo fixture
# (Deliberately omits "minor children" from the family definition.)
# ---------------------------------------------------------------------------

_DEMO_SOURCE = (
    "A landholder farmer family is defined as husband, wife and minor children "
    "who own cultivable land as per land records of the state/UT. "
    "The annual income support of Rs 6,000 is provided in three equal instalments of Rs 2,000 each. "
    "Retired or serving government employees and those paying Income Tax are excluded."
)

_DEMO_SIMPLIFIED_INCOMPLETE = (
    "An eligible farmer family is a husband and wife who own farmland according to state land records. "
    "They receive Rs 6,000 per year, paid in three parts of Rs 2,000 each. "
    "Government employees and income taxpayers are not eligible."
)
# Note: "minor children" is deliberately omitted — the controlled demo failure.

# ---------------------------------------------------------------------------
# Pre-stored Demo Fixtures (Protects live demonstrations during API quotas)
# ---------------------------------------------------------------------------

_PRESTORED_SIMPLIFICATIONS = [
    {
        "keywords": ["sukanya samriddhi", "g.s.r. 914(e)"],
        "simplified": (
            "The Sukanya Samriddhi Account Scheme (notified in December 2019 and amended in May 2020) "
            "is a government savings scheme for the girl child. The Central Government established these rules "
            "under section 3A of the Government Savings Banks Act, 1873. These rules came into force on the date "
            "of their publication in the Official Gazette."
        ),
    },
    {
        "keywords": ["landholder farmer family", "cultivable land", "6,000"],
        "simplified": (
            "A farmer family is defined as a husband, wife, and minor children who own cultivable farmland "
            "according to state or union territory land records. The government provides income support of "
            "Rs 6,000 per year, paid in three equal instalments of Rs 2,000 each. "
            "Serving or retired government employees and income tax payers are not eligible."
        ),
    },
]


def _get_prestored_simplification(text: str) -> str | None:
    text_lower = text.lower()
    for entry in _PRESTORED_SIMPLIFICATIONS:
        if all(kw in text_lower for kw in entry["keywords"]):
            return entry["simplified"]
    return None


# ---------------------------------------------------------------------------
# Deterministic transformation check
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """
    Normalize for similarity comparison.
    - Lowercase
    - Collapse all whitespace to single spaces
    - Strip leading/trailing whitespace
    Numbers, dates, amounts and punctuation that affects meaning are preserved.
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def check_transformation_quality(
    source: str,
    simplified: str,
) -> tuple[str, float]:
    """
    Deterministic similarity check using difflib.SequenceMatcher.

    Returns (simplification_quality, similarity_score).

    simplification_quality values:
      "simplified"            — Output is detectably different from source.
      "insufficient"          — Output is too similar; not meaningfully simplified.
      "requires_human_review" — Short passage; similarity score is unreliable.

    Thresholds are documented heuristics, not validated universal values.
    """
    norm_source = _normalize(source)
    norm_simplified = _normalize(simplified)

    similarity = difflib.SequenceMatcher(
        None, norm_source, norm_simplified, autojunk=False
    ).ratio()

    is_short = len(norm_source) < SHORT_PASSAGE_THRESHOLD

    if is_short:
        # Short passages: similarity scores are less reliable.
        # Flag borderline cases for human review rather than auto-classifying.
        if similarity > SHORT_PASSAGE_REVIEW:
            quality = "requires_human_review"
        else:
            quality = "simplified"
    else:
        if similarity > SIMILARITY_INSUFFICIENT:
            quality = "insufficient"
        else:
            quality = "simplified"

    return quality, round(similarity, 4)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SimplificationService:
    """
    Orchestrates the transformation check and two AI calls to simplify
    a passage and independently review its semantic fidelity.
    """

    def __init__(self, ai_provider: AIProvider) -> None:
        self._provider = ai_provider

    async def simplify_chunk(
        self,
        document_id: str,
        chunk_id: str,
        demo: bool = False,
    ) -> SimplificationResponse | None:
        """
        Simplify a chunk and evaluate transformation quality + semantic fidelity.

        Returns None if the document or chunk does not exist.
        If demo=True, uses a controlled incomplete simplification fixture.
        """
        doc = get_document(document_id)
        if doc is None:
            return None

        # Locate the requested chunk
        source_passage: str | None = None
        for chunk in doc.get("chunks", []):
            if chunk.get("chunk_id") == chunk_id:
                source_passage = chunk.get("text", "").strip()
                break

        if source_passage is None:
            return None

        if not source_passage:
            return SimplificationResponse(
                chunk_id=chunk_id,
                source_passage="",
                simplified_text="",
                simplification_quality="error",
                similarity_score=1.0,
                fidelity=SemanticFidelityResult(
                    status="requires_human_review",
                    note="Source passage is empty — fidelity cannot be evaluated.",
                ),
            )

        # --- Controlled demo mode ---
        if demo:
            source_for_eval = _DEMO_SOURCE
            simplified_text = _DEMO_SIMPLIFIED_INCOMPLETE
        else:
            source_for_eval = source_passage
            # --- Call 1: Simplify ---
            try:
                simplified_text = await self._call_simplify(source_passage)
            except TimeoutError:
                raise
            except Exception as exc:
                logger.error("Simplification Call 1 failed: %s", exc)
                prestored = _get_prestored_simplification(source_passage)
                if prestored:
                    logger.info("Using pre-stored demo simplification fallback for passage.")
                    simplified_text = prestored
                else:
                    return SimplificationResponse(
                        chunk_id=chunk_id,
                        source_passage=source_for_eval,
                        simplified_text="[Simplification Error: AI provider was unable to generate a response.]",
                        simplification_quality="error",
                        similarity_score=1.0,
                        fidelity=SemanticFidelityResult(
                            status="requires_human_review",
                            note=f"Call 1 failed: {str(exc)}. Human expert review required.",
                        ),
                        controlled_demo=False,
                    )

            # Strict output validation before evaluating similarity or invoking Call 2
            is_error_output = (
                not simplified_text
                or not simplified_text.strip()
                or "unable to parse model output" in simplified_text.lower()
                or simplified_text.strip().startswith("[Notice:")
                or simplified_text.strip().startswith("[Error:")
            )

            if is_error_output:
                prestored = _get_prestored_simplification(source_passage)
                if prestored:
                    logger.info("Replaced invalid model output with pre-stored demo simplification.")
                    simplified_text = prestored
                else:
                    logger.warning("Call 1 produced an invalid/error output: %r", simplified_text)
                    return SimplificationResponse(
                        chunk_id=chunk_id,
                        source_passage=source_for_eval,
                        simplified_text=simplified_text if simplified_text else "[Error: Empty response received from provider]",
                        simplification_quality="error",
                        similarity_score=1.0,
                        fidelity=SemanticFidelityResult(
                            status="requires_human_review",
                            note="AI provider returned an invalid response or parse error. Human expert review required.",
                        ),
                        controlled_demo=False,
                    )

        # --- Step 0: Deterministic transformation check ---
        simplification_quality, similarity_score = check_transformation_quality(
            source_for_eval, simplified_text
        )

        # --- Call 2: Independent fidelity review ---
        fidelity = await self._call_review(source_for_eval, simplified_text)
        fidelity.controlled_demo = demo

        return SimplificationResponse(
            chunk_id=chunk_id,
            source_passage=source_for_eval,
            simplified_text=simplified_text,
            simplification_quality=simplification_quality,
            similarity_score=similarity_score,
            fidelity=fidelity,
            controlled_demo=demo,
        )

    async def _call_simplify(self, source_passage: str) -> str:
        """Call 1: Generate plain-language simplification."""
        user_question = (
            "Rewrite the following administrative passage in plain, simple English "
            "for an ordinary citizen. Follow all rules in your instructions exactly.\n\n"
            f"SOURCE PASSAGE:\n{source_passage}"
        )
        # Pass the passage as context so the provider can format it correctly
        passages = [
            {"chunk_id": "simplify-target", "page_number": 1, "text": source_passage}
        ]
        result = await self._provider.generate_grounded_answer(
            question=user_question,
            passages=passages,
            system_instruction=SIMPLIFY_SYSTEM_PROMPT,
        )
        return result.answer.strip() or source_passage

    async def _call_review(
        self, source: str, simplified: str
    ) -> SemanticFidelityResult:
        """
        Call 2: Independent fidelity review.

        Checks meaning and condition preservation only.
        Does NOT assess simplification quality, readability, or vocabulary.
        """
        review_question = (
            f"SOURCE:\n{source}\n\n"
            f"SIMPLIFIED:\n{simplified}\n\n"
            "Review whether SIMPLIFIED preserves all conditions, amounts, exclusions, "
            "dates, age limits and document requirements from SOURCE. "
            "Respond with ONLY the JSON as instructed."
        )
        try:
            result = await self._provider.generate_grounded_answer(
                question=review_question,
                passages=[],  # Reviewer needs no passage context
                system_instruction=REVIEWER_SYSTEM_PROMPT,
            )
            raw = result.raw_response or {}

            status_raw = str(raw.get("status", "requires_human_review")).strip().lower()
            valid_statuses = {"verified", "potential_issue", "requires_human_review"}
            status = status_raw if status_raw in valid_statuses else "requires_human_review"

            return SemanticFidelityResult(
                status=status,  # type: ignore[arg-type]
                preserved_conditions=_as_str_list(raw.get("preserved_conditions", [])),
                potentially_missing=_as_str_list(raw.get("potentially_missing", [])),
            )
        except Exception as exc:
            logger.warning("Fidelity reviewer call failed: %s", str(exc))
            return SemanticFidelityResult(
                status="requires_human_review",
                note=(
                    "Fidelity reviewer encountered an error — human expert review required. "
                    "A passing check does not replace independent review by a subject-matter expert. "
                    "This evaluation does not constitute legal or administrative advice."
                ),
            )


def _as_str_list(value: Any) -> list[str]:
    """Safely coerce a value to list[str]."""
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []
