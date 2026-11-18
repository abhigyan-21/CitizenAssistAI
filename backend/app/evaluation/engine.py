"""
Unified CDTM Evaluation Engine (Phase 6).

Integrates all five dimensions of the Citizen Document Trustworthiness Model:
  a. Source Fidelity (extraction quality, selectable text, reference comparison)
  b. Semantic Fidelity (preservation of meaning, rules, exclusions during simplification)
  c. Evidence Grounding (claim-level support against cited source passages)
  d. Cross-Lingual Fidelity (preservation of numbers, rules, conditions across languages)
  e. Citizen Accessibility (structural readability proxies, unexplained acronyms)

CRITICAL INVARIANTS:
1. Returns five independent dimension reports.
2. NEVER generates a composite score, weighted score, ranking, or single overall trust verdict.
3. NEVER marks Citizen Accessibility verified based on readability or jargon checks alone.
4. Returns 'not_evaluated' when required evaluation inputs are unavailable.
"""
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field

from app.ai.base import AIProvider
from app.document.store import get_document
from app.evaluation.accessibility import (
    CitizenAccessibilityResult,
    evaluate_accessibility,
)
from app.evaluation.cross_lingual_fidelity import CrossLingualFidelityResult
from app.evaluation.evidence_grounding import (
    EvidenceGroundingEvaluator,
    EvidenceGroundingResult,
)
from app.evaluation.semantic_fidelity import SemanticFidelityResult
from app.evaluation.source_fidelity import (
    SourceFidelityResult,
    evaluate_source_fidelity,
)


class CDTMReport(BaseModel):
    """
    Multidimensional CDTM Evaluation Report.

    Presents individual evaluation findings across the five distinct dimensions.
    Deliberately omits any composite, aggregated, or weighted trust score.
    """

    document_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 evaluation timestamp.",
    )
    # Dimension a: Source Fidelity
    source_fidelity: SourceFidelityResult
    # Dimension b: Semantic Fidelity
    semantic_fidelity: SemanticFidelityResult
    # Dimension c: Evidence Grounding
    evidence_grounding: EvidenceGroundingResult
    # Dimension d: Cross-Lingual Fidelity
    cross_lingual_fidelity: CrossLingualFidelityResult
    # Dimension e: Citizen Accessibility
    citizen_accessibility: CitizenAccessibilityResult

    methodological_disclaimer: str = Field(
        default=(
            "CDTM Multidimensional Evaluation Report: Each dimension is evaluated independently. "
            "No composite or overall trust score is calculated. Automated AI reviews and structural "
            "proxies do not substitute for human subject-matter expert or citizen verification."
        )
    )
    controlled_demo: bool = Field(
        default=False,
        description="True if any dimension within this report ran under a controlled failure demo fixture.",
    )


class CDTMEvaluationEngine:
    """Orchestrates independent evaluation across all five CDTM dimensions."""

    def __init__(self, ai_provider: AIProvider | None = None) -> None:
        self._provider = ai_provider
        self._grounding_evaluator = EvidenceGroundingEvaluator(ai_provider=ai_provider)

    async def generate_document_report(
        self,
        document_id: str,
        last_qa_result: dict[str, Any] | None = None,
        last_simplification: dict[str, Any] | None = None,
        last_translation: dict[str, Any] | None = None,
        reference_text: str | None = None,
        demo: bool = False,
    ) -> CDTMReport:
        """
        Compile independent evaluation reports for a document across all five CDTM dimensions.
        Returns 'not_evaluated' for dimensions whose operational inputs have not been run.
        """
        doc = get_document(document_id)
        chunks = doc.get("chunks", []) if doc else []

        # --- 1. Dimension a: Source Fidelity ---
        if doc:
            # Reconstruct basic page data from chunks
            pages_dict: dict[int, list[str]] = {}
            for c in chunks:
                p_num = c.get("page_number", 1)
                pages_dict.setdefault(p_num, []).append(c.get("text", ""))

            pages_list = [
                {"page_number": p, "text": " ".join(t)}
                for p, t in sorted(pages_dict.items())
            ]
            extraction_dict = {
                "page_count": len(pages_list),
                "pages": pages_list,
                "warnings": [],
            }
            if demo:
                source_fidelity_res = SourceFidelityResult(
                    status="verified",
                    page_count=len(pages_list) or 4,
                    pages_with_text=len(pages_list) or 4,
                    pages_without_text=0,
                    warnings=[],
                    has_reference_comparison=True,
                    reference_match=True,
                    note="Verified text extraction compared against Gazette of India G.S.R. 914(E) reference text.",
                    controlled_demo=True,
                )
            else:
                source_fidelity_res = evaluate_source_fidelity(
                    extraction_result=extraction_dict,
                    reference_text=reference_text,
                    demo=demo,
                )
        else:
            source_fidelity_res = SourceFidelityResult(
                status="not_evaluated",
                note=f"Document '{document_id}' not found in store.",
                controlled_demo=demo,
            )

        # --- 2. Dimension b: Semantic Fidelity ---
        if last_simplification and "fidelity" in last_simplification:
            raw_sf = last_simplification["fidelity"]
            if isinstance(raw_sf, SemanticFidelityResult):
                semantic_fidelity_res = raw_sf
            elif isinstance(raw_sf, dict):
                semantic_fidelity_res = SemanticFidelityResult(**raw_sf)
            else:
                semantic_fidelity_res = SemanticFidelityResult(
                    status="not_evaluated",
                    note="Invalid simplification fidelity payload.",
                )
        elif demo:
            semantic_fidelity_res = SemanticFidelityResult(
                status="verified",
                preserved_conditions=[
                    "₹250 minimum opening deposit",
                    "₹1,50,000 maximum annual deposit limit",
                    "Account opened for girl child until age of 10 years",
                    "Deposits allowed up to 15 years from opening date",
                    "21-year account maturity from opening date",
                    "50% withdrawal for higher education after 10th standard or age 18",
                ],
                potentially_missing=[],
                controlled_demo=True,
                note="Verified section-matched plain-language simplification for Sukanya Samriddhi Scheme.",
            )
        else:
            semantic_fidelity_res = SemanticFidelityResult(
                status="not_evaluated",
                note="No plain-language simplification has been evaluated for this document.",
                controlled_demo=demo,
            )

        # --- 3. Dimension c: Evidence Grounding ---
        if last_qa_result:
            answer = last_qa_result.get("answer", "")
            cited_ids = last_qa_result.get("cited_chunk_ids", [])
            insufficient = last_qa_result.get("insufficient_evidence", False)
            evidence_grounding_res = await self._grounding_evaluator.evaluate_grounding(
                document_id=document_id,
                answer=answer,
                cited_chunk_ids=cited_ids,
                insufficient_evidence=insufficient,
                demo=demo,
            )
        elif demo:
            evidence_grounding_res = EvidenceGroundingResult(
                status="grounded",
                cited_chunk_ids=["chunk-p1-c0", "chunk-p2-c1", "chunk-p3-c0"],
                valid_chunk_ids=["chunk-p1-c0", "chunk-p2-c1", "chunk-p3-c0"],
                invalid_chunk_ids=[],
                claims=[
                    ClaimSupportItem(
                        claim="The minimum initial deposit to open an account is ₹250.",
                        supported=True,
                        citing_chunk_ids=["chunk-p1-c0"],
                        reasoning="Directly stated in Section 4(1) of the Scheme Rules.",
                    ),
                    ClaimSupportItem(
                        claim="Deposits can be made in multiples of ₹50 up to ₹1,50,000 per financial year.",
                        supported=True,
                        citing_chunk_ids=["chunk-p1-c0"],
                        reasoning="Directly confirmed by Section 4(1) of the Scheme Rules.",
                    ),
                    ClaimSupportItem(
                        claim="Partial withdrawal up to 50% is permitted for higher education after 10th standard.",
                        supported=True,
                        citing_chunk_ids=["chunk-p3-c0"],
                        reasoning="Explicitly authorized under Section 8(1) of the Scheme Rules.",
                    ),
                ],
                supported_claims_count=3,
                unsupported_claims_count=0,
                note="All atomic claims corroborated by cited Sukanya Samriddhi Scheme clauses.",
                controlled_demo=True,
            )
        else:
            evidence_grounding_res = EvidenceGroundingResult(
                status="not_evaluated",
                note="No question-answering inquiry has been evaluated for this document.",
                controlled_demo=demo,
            )

        # --- 4. Dimension d: Cross-Lingual Fidelity ---
        if last_translation and "fidelity" in last_translation:
            raw_clf = last_translation["fidelity"]
            if isinstance(raw_clf, CrossLingualFidelityResult):
                cross_lingual_fidelity_res = raw_clf
            elif isinstance(raw_clf, dict):
                cross_lingual_fidelity_res = CrossLingualFidelityResult(**raw_clf)
            else:
                cross_lingual_fidelity_res = CrossLingualFidelityResult(
                    status="not_evaluated",
                    note="Invalid cross-lingual fidelity payload.",
                )
        elif demo:
            cross_lingual_fidelity_res = CrossLingualFidelityResult(
                status="verified",
                preserved_terms=[
                    "₹250 (दो सौ पचास रुपये) न्यूनतम जमा राशि",
                    "₹1,50,000 (एक लाख पचास हजार रुपये) अधिकतम वार्षिक सीमा",
                    "10 वर्ष की आयु तक खाता खोलने की पात्रता",
                    "15 वर्ष तक जमा करने की अवधि",
                    "21 वर्ष में खाते की परिपक्वता (Maturity)",
                    "50% उच्च शिक्षा हेतु आंशिक निकासी",
                ],
                potentially_divergent=[],
                note="Verified English-to-Hindi Devanagari translation with numerals, rules, and conditions intact.",
            )
        else:
            cross_lingual_fidelity_res = CrossLingualFidelityResult(
                status="not_evaluated",
                note="No cross-lingual translation has been evaluated for this document.",
            )

        # --- 5. Dimension e: Citizen Accessibility ---
        sample_text = ""
        if chunks:
            sample_text = " ".join(c.get("text", "") for c in chunks[:3])
        if sample_text:
            citizen_accessibility_res = evaluate_accessibility(
                text=sample_text,
                language="en",
                demo=demo,
            )
        else:
            citizen_accessibility_res = evaluate_accessibility(
                text="No document text available.",
                language="en",
                demo=demo,
            )

        return CDTMReport(
            document_id=document_id,
            source_fidelity=source_fidelity_res,
            semantic_fidelity=semantic_fidelity_res,
            evidence_grounding=evidence_grounding_res,
            cross_lingual_fidelity=cross_lingual_fidelity_res,
            citizen_accessibility=citizen_accessibility_res,
            controlled_demo=demo,
        )
