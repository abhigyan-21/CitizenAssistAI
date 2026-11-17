"""
Cross-Lingual Fidelity result schema for CDTM dimension d.

Returned by TranslationService after:
  Call 1 — English to Hindi translation (Devanagari)
  Step 0 — Deterministic entity and term preservation check
  Call 2 — AI review pass (meaning, negation, eligibility, deadlines)

Deterministic checks and Call 2 AI review are kept strictly separate.
Call 2 is a separate AI review pass, not independent ground-truth verification.
"""
from typing import Literal
from pydantic import BaseModel, Field


class CrossLingualFidelityResult(BaseModel):
    """
    Result of the second-pass AI review for Cross-Lingual Fidelity.

    Assesses whether meaning, eligibility conditions, exclusions, negation,
    and deadline interpretations were faithfully preserved between the English
    source passage and the Hindi translation.

    Note: This is a separate AI review pass using the configured model. It is
    NOT independent ground truth. Bilingual subject-matter expert verification
    remains necessary for official or legal use.
    """

    status: Literal["verified", "potential_issue", "requires_human_review", "not_evaluated"] = Field(
        description="Cross-lingual semantic fidelity assessment by AI review pass."
    )
    preserved_terms: list[str] = Field(
        default_factory=list,
        description="Conditions, terms, or entities confirmed preserved in the translation.",
    )
    potentially_divergent: list[str] = Field(
        default_factory=list,
        description="Items flagged as omitted, altered, inverted, or divergent.",
    )
    note: str = Field(
        default=(
            "AI-assisted cross-lingual fidelity review — results require human expert verification. "
            "Call 2 is a secondary AI review pass, not independent verification. "
            "This evaluation does not constitute certified legal translation or administrative advice."
        ),
        description="Mandatory research and legal disclaimer.",
    )


class TranslationResponse(BaseModel):
    """
    Full response returned by the translation endpoint.

    Keeps deterministic entity/term preservation and AI semantic review separate.
    Records input provenance (whether the source was an original or simplified chunk).
    """

    chunk_id: str
    source_english: str
    translated_hindi: str
    target_language: Literal["hi"] = "hi"
    input_variant: Literal["original", "simplified"] = Field(
        default="original",
        description="Provenance of the input passage: 'original' document chunk or 'simplified' English text.",
    )
    term_preservation_status: Literal["intact", "partial", "requires_human_review"] = Field(
        description=(
            "Deterministic check of numbers, amounts, dates, and administrative terms. "
            "Independent of AI semantic fidelity review."
        )
    )
    fidelity: CrossLingualFidelityResult = Field(
        description="AI review pass evaluating semantic fidelity, negation, and eligibility conditions."
    )
    controlled_demo: bool = Field(
        default=False,
        description="True when this translation was processed under controlled failure demonstration mode.",
    )


class HindiSimplificationResponse(BaseModel):
    """
    Response schema for Phase 5 Hindi Plain-Language Simplification (सरल हिंदी).
    """

    chunk_id: str
    formal_hindi: str
    simplified_hindi: str
    term_preservation_status: Literal["intact", "partial", "requires_human_review"] = Field(
        description="Deterministic check verifying numbers and statutory figures are preserved in simplified Hindi."
    )
    preserved_terms: list[str] = Field(
        default_factory=list,
        description="Entities and figures confirmed present in the simplified Hindi.",
    )
    missing_terms: list[str] = Field(
        default_factory=list,
        description="Entities or figures from the original passage possibly absent in simplified Hindi.",
    )
