"""
Semantic Fidelity result schema for CDTM dimension b.

Returned by the SimplificationService after a two-call AI pipeline:
  Call 1 — simplification
  Call 2 — independent fidelity review (meaning/condition preservation only)

The transformation quality check is deterministic (difflib.SequenceMatcher)
and is kept separate from the fidelity review.
"""
from typing import Literal
from pydantic import BaseModel, Field


class SemanticFidelityResult(BaseModel):
    """
    Result of the independent AI-assisted fidelity review (Call 2).

    Assesses whether meaning, conditions, exclusions, amounts, dates and
    document requirements were preserved in the simplified text.

    Status values:
      verified              — Reviewer found no missing conditions or amounts.
      potential_issue       — Reviewer flagged one or more possibly missing items.
      requires_human_review — Reviewer was uncertain or the passage is complex.
    """

    status: Literal["verified", "potential_issue", "requires_human_review", "not_evaluated"] = Field(
        description="Semantic fidelity assessment: were meaning and conditions preserved?"
    )
    preserved_conditions: list[str] = Field(
        default_factory=list,
        description="Conditions, amounts or terms the reviewer confirmed are present in the simplified text.",
    )
    potentially_missing: list[str] = Field(
        default_factory=list,
        description="Conditions, amounts or terms the reviewer flagged as possibly absent or altered.",
    )
    controlled_demo: bool = Field(
        default=False,
        description="True when this result was produced by the controlled failure demonstration mode.",
    )
    note: str = Field(
        default=(
            "AI-assisted fidelity review — results require human expert verification. "
            "A passing check does not replace independent review by a subject-matter expert. "
            "This evaluation does not constitute legal or administrative advice."
        ),
        description="Mandatory disclaimer attached to every fidelity result.",
    )


class SimplificationResponse(BaseModel):
    """
    Full response returned by the simplify endpoint.

    simplification_quality and fidelity are independent assessments and
    must be displayed separately in the UI.

    simplification_quality values:
      simplified            — Output is detectably different from the source.
      insufficient          — Output is too similar to the source; not simplified.
      requires_human_review — Source is short; similarity score is unreliable.
      error                 — Simplification call failed.
    """

    chunk_id: str
    source_passage: str
    simplified_text: str
    simplification_quality: Literal[
        "simplified", "insufficient", "requires_human_review", "error"
    ] = Field(
        description=(
            "Deterministic transformation check: was the output detectably different from the source? "
            "Independent of the AI-assisted fidelity review."
        )
    )
    similarity_score: float = Field(
        description="Normalized character-sequence similarity (0–1). Lower is more simplified.",
    )
    fidelity: SemanticFidelityResult = Field(
        description=(
            "AI-assisted fidelity review: were meaning and critical conditions preserved? "
            "Independent of simplification_quality."
        )
    )
    controlled_demo: bool = False
