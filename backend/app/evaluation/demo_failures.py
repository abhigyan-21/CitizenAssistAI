"""
Controlled Failure Demonstrations for all five CDTM dimensions.

Allows research demonstrators to trigger and observe deliberate failure detection:
  Dimension a (Source Fidelity): Incomplete extraction with image-only page warning.
  Dimension b (Semantic Fidelity): Omission of critical eligibility condition.
  Dimension c (Evidence Grounding): Answer claiming unsupported financial figures.
  Dimension d (Cross-Lingual Fidelity): Reversed eligibility condition in Hindi.
  Dimension e (Citizen Accessibility): Complex bureaucratic prose with unexplained acronyms.

CRITICAL INVARIANTS:
1. Every failure runs through actual evaluation logic.
2. Never forces a successful detection status; reports output honestly.
3. Never mutates uploaded documents or stored chunks.
4. Clearly marked as controlled demonstration fixtures.
"""
from typing import Any

from app.document.store import get_document
from app.evaluation.accessibility import (
    CitizenAccessibilityResult,
    evaluate_accessibility,
)
from app.evaluation.evidence_grounding import (
    EvidenceGroundingEvaluator,
    EvidenceGroundingResult,
)
from app.evaluation.source_fidelity import (
    SourceFidelityResult,
    evaluate_source_fidelity,
)
from app.services.simplification_service import SimplificationService
from app.services.translation_service import TranslationService


def run_source_fidelity_demo() -> SourceFidelityResult:
    """
    Demonstrate Source Fidelity failure detection.
    Passes an incomplete extraction fixture (Page 2 is scanned/image-only without text)
    through the actual evaluate_source_fidelity function.
    """
    fixture_extraction = {
        "page_count": 2,
        "pages": [
            {"page_number": 1, "text": "Page 1 contains standard administrative text."},
            {"page_number": 2, "text": ""},  # Empty/image-only page
        ],
        "warnings": ["Page 2 has no selectable text; OCR may be required."],
    }
    return evaluate_source_fidelity(extraction_result=fixture_extraction, demo=True)


async def run_evidence_grounding_demo(
    document_id: str,
    evaluator: EvidenceGroundingEvaluator,
) -> EvidenceGroundingResult:
    """
    Demonstrate Evidence Grounding failure detection.
    Passes an answer that makes a deliberately unsupported claim (e.g. Rs 50,000 monthly cash)
    through the actual claim-level AI evaluator against real stored passages.
    """
    doc = get_document(document_id)
    chunks = doc.get("chunks", []) if doc else []
    first_chunk_id = chunks[0]["chunk_id"] if chunks else "dummy-chunk-id"

    # Unsupported claim: Rs 50,000 monthly benefit (nowhere in source guidelines)
    unsupported_answer = (
        "Under this scheme, all registered citizens receive Rs 50,000 per month in unconditional cash transfers. "
        "No application or eligibility verification is needed."
    )

    return await evaluator.evaluate_grounding(
        document_id=document_id,
        answer=unsupported_answer,
        cited_chunk_ids=[first_chunk_id],
        insufficient_evidence=False,
        demo=True,
    )


async def run_semantic_fidelity_demo(
    document_id: str,
    chunk_id: str,
    service: SimplificationService,
) -> Any:
    """
    Demonstrate Semantic Fidelity failure detection.
    Reuses Phase 4 controlled demo fixture where 'minor children' is omitted.
    """
    return await service.simplify_chunk(document_id=document_id, chunk_id=chunk_id, demo=True)


async def run_cross_lingual_demo(
    document_id: str,
    chunk_id: str,
    service: TranslationService,
) -> Any:
    """
    Demonstrate Cross-Lingual Fidelity failure detection.
    Reuses Phase 5 controlled demo where eligibility condition is inverted in Hindi.
    """
    return await service.translate_chunk(document_id=document_id, chunk_id=chunk_id, demo=True)


def run_accessibility_demo() -> CitizenAccessibilityResult:
    """
    Demonstrate Citizen Accessibility structural barrier detection.
    Evaluates complex bureaucratic text containing multiple unexplained acronyms
    (DBT, UT, KCC without expansion) and very low readability.
    """
    dense_text = (
        "Pursuant to the administrative notification under Section 4(b), the beneficiary family "
        "domiciled within the relevant UT shall effectuate DBT reconciliations through KCC modalities "
        "interfacing with the nodal authority prior to sub-clause disbursements."
    )
    return evaluate_accessibility(text=dense_text, language="en", demo=True)
