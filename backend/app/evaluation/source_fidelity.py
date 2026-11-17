"""
Source Fidelity evaluation module for CDTM dimension a.

Evaluates whether document extraction faithfully preserved source content.
Assesses page count, selectable text presence, empty/image-only pages,
and PyMuPDF extraction warnings.

CRITICAL INVARIANT:
Selectable text and an absence of extraction warnings do NOT prove faithful extraction.
Only mark 'verified' when extraction has been compared against a trusted reference
or rendered source content. Without a reference comparison, clean extractions
must remain 'not_evaluated'.
"""
from typing import Any, Literal
from pydantic import BaseModel, Field


class SourceFidelityResult(BaseModel):
    """
    Evaluation result for CDTM Dimension a: Source Fidelity.

    Statuses:
      verified        — Extraction was explicitly validated against a trusted reference
                        or rendered source content.
      requires_review — Page warnings exist (e.g. image-only pages, missing text) or
                        mismatch against trusted reference detected.
      not_evaluated   — Selectable text was extracted without warnings, but no comparison
                        against rendered visual pages or reference content has been performed.
    """

    status: Literal["verified", "requires_review", "not_evaluated"] = Field(
        description="Source Fidelity status: verified, requires_review, or not_evaluated."
    )
    page_count: int = Field(default=0, description="Total page count of the source document.")
    pages_with_text: int = Field(default=0, description="Count of pages containing selectable text.")
    pages_without_text: int = Field(default=0, description="Count of pages with zero selectable text.")
    warnings: list[str] = Field(default_factory=list, description="Extraction warnings emitted by parser.")
    has_reference_comparison: bool = Field(
        default=False,
        description="Whether extraction was compared against a ground-truth reference or rendered content.",
    )
    reference_match: bool | None = Field(
        default=None,
        description="True if reference comparison matched; False if mismatch; None if uncompared.",
    )
    note: str = Field(
        description="Explanatory assessment note with explicit methodological limitations."
    )
    controlled_demo: bool = Field(
        default=False,
        description="True when evaluated under controlled failure demonstration mode.",
    )


def evaluate_source_fidelity(
    extraction_result: dict[str, Any],
    reference_text: str | None = None,
    demo: bool = False,
) -> SourceFidelityResult:
    """
    Evaluate Source Fidelity for an extracted PDF document.

    If demo=True, evaluates with a controlled fixture or altered extraction input,
    running through actual evaluation logic.
    """
    page_count = extraction_result.get("page_count", 0)
    pages = extraction_result.get("pages", [])
    warnings = list(extraction_result.get("warnings", []))

    pages_with_text = 0
    pages_without_text = 0

    for page in pages:
        text = page.get("text", "").strip()
        if text:
            pages_with_text += 1
        else:
            pages_without_text += 1

    # Check for empty or unparseable document
    if page_count == 0 or (pages_with_text == 0 and page_count > 0):
        return SourceFidelityResult(
            status="requires_review",
            page_count=page_count,
            pages_with_text=pages_with_text,
            pages_without_text=pages_without_text,
            warnings=warnings or ["Document contains zero selectable text across all pages."],
            has_reference_comparison=bool(reference_text),
            reference_match=False if reference_text else None,
            note="Extraction failed to retrieve selectable text. OCR or manual review required.",
            controlled_demo=demo,
        )

    # If warnings exist (e.g. image-only pages, partial extraction failures)
    if pages_without_text > 0 or warnings:
        return SourceFidelityResult(
            status="requires_review",
            page_count=page_count,
            pages_with_text=pages_with_text,
            pages_without_text=pages_without_text,
            warnings=warnings,
            has_reference_comparison=bool(reference_text),
            reference_match=False if reference_text else None,
            note=(
                f"Extraction flagged warnings: {pages_without_text} page(s) lack selectable text. "
                "Image-only content or complex tabular layouts may be missing without OCR."
            ),
            controlled_demo=demo,
        )

    # Clean extraction with selectable text on all pages
    if reference_text is not None:
        # Compare extracted full text against trusted reference
        full_extracted = " ".join(p.get("text", "") for p in pages).strip()
        # Clean whitespace comparison
        norm_extracted = " ".join(full_extracted.split())
        norm_ref = " ".join(reference_text.split())

        matched = norm_extracted == norm_ref or norm_ref in norm_extracted
        if matched:
            return SourceFidelityResult(
                status="verified",
                page_count=page_count,
                pages_with_text=pages_with_text,
                pages_without_text=0,
                warnings=[],
                has_reference_comparison=True,
                reference_match=True,
                note="Extraction verified against trusted reference content with full selectable text.",
                controlled_demo=demo,
            )
        else:
            return SourceFidelityResult(
                status="requires_review",
                page_count=page_count,
                pages_with_text=pages_with_text,
                pages_without_text=0,
                warnings=["Extracted content diverges from ground-truth reference text."],
                has_reference_comparison=True,
                reference_match=False,
                note="Extracted text diverges from the provided reference. Manual verification required.",
                controlled_demo=demo,
            )

    # Invariant: No reference comparison provided -> NOT EVALUATED
    return SourceFidelityResult(
        status="not_evaluated",
        page_count=page_count,
        pages_with_text=pages_with_text,
        pages_without_text=0,
        warnings=[],
        has_reference_comparison=False,
        reference_match=None,
        note=(
            "Selectable text extracted on all pages without PyMuPDF warnings. "
            "However, extraction has not been validated against rendered visual source pages "
            "or a trusted reference. CDTM Source Fidelity remains not_evaluated."
        ),
        controlled_demo=demo,
    )
