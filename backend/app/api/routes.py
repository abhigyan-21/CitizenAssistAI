from typing import Any, Literal
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

import groq as groq_sdk

from app.core.config import settings
from app.document.pdf_extractor import extract_pdf
from app.document.store import get_document, save_document, search_document
from app.services.qa_service import QAService
from app.services.simplification_service import SimplificationService
from app.services.translation_service import TranslationService
from app.evaluation.engine import CDTMEvaluationEngine
from app.evaluation.evidence_grounding import EvidenceGroundingEvaluator
from app.evaluation.demo_failures import (
    run_accessibility_demo,
    run_cross_lingual_demo,
    run_evidence_grounding_demo,
    run_semantic_fidelity_demo,
    run_source_fidelity_demo,
)

router = APIRouter(prefix="/api", tags=["documents"])

_qa_service: QAService = QAService()


def get_qa_service() -> QAService:
    """Return the active QAService instance."""
    return _qa_service


def set_qa_service(service: QAService) -> None:
    """Set the active QAService instance (used in automated tests)."""
    global _qa_service
    _qa_service = service


class SearchRequest(BaseModel):
    query: str = Field(default="", description="Search query string")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of chunks to return")
    document_id: str | None = Field(default=None, description="Document ID (optional when in URL path)")


class AskRequest(BaseModel):
    query: str | None = Field(default=None, description="Citizen inquiry question")
    question: str | None = Field(default=None, description="Citizen inquiry question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of passages to retrieve for grounding")
    mode: Literal["cdtm", "basic"] = Field(
        default="cdtm",
        description="Generation mode: 'cdtm' (grounded + audited) or 'basic' (baseline unverified)",
    )

    def get_question(self) -> str:
        """Extract question from either 'query' or 'question' field."""
        return (self.query or self.question or "").strip()


@router.post("/documents/extract")
async def extract_document(file: UploadFile = File(...)):
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf") or file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Please upload a PDF file.")

    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF exceeds the upload size limit.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")

    try:
        result = extract_pdf(content)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Could not read this PDF.") from exc

    # Automatically persist chunks and initialize BM25 index in memory store
    save_document(
        document_id=result["document_id"],
        filename=filename,
        chunks=result["chunks"],
    )

    return {
        "filename": filename,
        **result,
        "source_fidelity_status": "requires_review" if result["warnings"] else "not_evaluated",
    }


@router.post("/documents/{document_id}/search")
async def search_document_by_id(document_id: str, request: SearchRequest):
    results = search_document(document_id, request.query, request.top_k)
    if results is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    return {
        "document_id": document_id,
        "query": request.query,
        "total_results": len(results),
        "results": results,
    }


@router.post("/documents/search")
async def search_document_body(request: SearchRequest):
    if not request.document_id:
        raise HTTPException(
            status_code=400,
            detail="Field 'document_id' is required when searching via this endpoint.",
        )
    return await search_document_by_id(request.document_id, request)


@router.post("/documents/{document_id}/ask")
async def ask_document(document_id: str, request: AskRequest):
    """
    Evidence-grounded Question Answering endpoint (Milestone 5).
    Retrieves BM25 passages, queries Gemini/Groq, validates citations, and returns grounded answer.
    """
    question = request.get_question()
    if not question:
        raise HTTPException(
            status_code=422,
            detail="The inquiry question cannot be empty.",
        )

    try:
        service = get_qa_service()
        response = await service.answer_question(
            document_id=document_id,
            question=question,
            top_k=request.top_k,
            mode=request.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="The AI provider request timed out.") from exc
    except groq_sdk.RateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="Groq API rate limit or quota exceeded. Please wait a moment before trying again.",
        ) from exc
    except groq_sdk.APIStatusError as exc:
        status = getattr(exc, "status_code", None)
        if status == 429:
            raise HTTPException(
                status_code=429,
                detail="AI provider rate limit exceeded. Please wait a moment.",
            ) from exc
        raise HTTPException(status_code=502, detail="AI provider returned an error.") from exc
    except Exception as exc:
        err_msg = str(exc)
        code = getattr(exc, "code", None)
        if code == 429 or "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit or quota exceeded. Please wait a moment before trying again.",
            ) from exc
        raise HTTPException(status_code=502, detail=f"AI provider error: {err_msg}") from exc

    if response is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    return response


# ---------------------------------------------------------------------------
# Phase 4: Semantic Fidelity — Simplification endpoint
# ---------------------------------------------------------------------------

@router.post("/documents/{document_id}/chunks/{chunk_id}/simplify")
async def simplify_chunk(
    document_id: str,
    chunk_id: str,
    demo: bool = Query(default=False, description="Trigger controlled failure demonstration"),
):
    """
    Phase 4 — Semantic Fidelity.
    Simplifies a source passage (Call 1) and independently reviews the
    simplification for missing conditions, amounts or exclusions (Call 2).
    """
    service = get_qa_service()
    is_demo = bool(demo.default) if hasattr(demo, "default") else bool(demo)
    simplification_service = SimplificationService(ai_provider=service._ai_provider)
    if simplification_service._provider is None:
        try:
            simplification_service._provider = service.get_provider()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        result = await simplification_service.simplify_chunk(
            document_id=document_id,
            chunk_id=chunk_id,
            demo=is_demo,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider request timed out.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except groq_sdk.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="AI provider rate limit exceeded.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(exc)}") from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' or chunk '{chunk_id}' not found.",
        )

    return result


# ---------------------------------------------------------------------------
# Phase 5: Cross-Lingual Fidelity — Translation endpoint (English -> Hindi)
# ---------------------------------------------------------------------------

class TranslateRequest(BaseModel):
    simplified_text: str | None = Field(
        default=None,
        description="Optional simplified English text if translating from a simplified variant.",
    )


@router.post("/documents/{document_id}/chunks/{chunk_id}/translate")
async def translate_chunk(
    document_id: str,
    chunk_id: str,
    target_language: str = Query(default="hi", description="Target language ('hi')"),
    demo: bool = Query(default=False, description="Trigger controlled failure demonstration"),
    input_variant: str = Query(default="original", description="Input provenance: 'original' or 'simplified'"),
    body: TranslateRequest | None = None,
):
    """
    Phase 5 — Cross-Lingual Fidelity (English -> Hindi).
    Translates an English passage to Hindi (Call 1), deterministically checks
    term and numerical preservation (Step 0), and performs a secondary AI review pass
    evaluating semantic and condition preservation (Call 2).
    """
    service = get_qa_service()
    is_demo = bool(demo.default) if hasattr(demo, "default") else bool(demo)
    translation_service = TranslationService(ai_provider=service._ai_provider)
    if translation_service._provider is None:
        try:
            translation_service._provider = service.get_provider()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    simplified_text = body.simplified_text if body else None

    try:
        result = await translation_service.translate_chunk(
            document_id=document_id,
            chunk_id=chunk_id,
            target_language=target_language,
            demo=is_demo,
            input_variant=input_variant,
            simplified_text=simplified_text,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider request timed out.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except groq_sdk.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="AI provider rate limit exceeded.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(exc)}") from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' or chunk '{chunk_id}' not found.",
        )

    return result


class SimplifyHindiRequest(BaseModel):
    hindi_text: str | None = Field(
        default=None,
        description="Optional formal Hindi text to simplify. If omitted, uses chunk's translation.",
    )


@router.post("/documents/{document_id}/chunks/{chunk_id}/simplify-hindi")
async def simplify_hindi_chunk(
    document_id: str,
    chunk_id: str,
    body: SimplifyHindiRequest | None = None,
):
    """
    Phase 5 — Plain-Language Hindi Simplification (सरल हिंदी).
    Rewrites formal administrative Hindi into simple, citizen-friendly everyday Hindi
    and verifies that all figures and dates remain intact.
    """
    service = get_qa_service()
    translation_service = TranslationService(ai_provider=service._ai_provider)
    if translation_service._provider is None:
        try:
            translation_service._provider = service.get_provider()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    hindi_text = body.hindi_text if body else None

    try:
        result = await translation_service.simplify_hindi(
            document_id=document_id,
            chunk_id=chunk_id,
            hindi_text=hindi_text,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider request timed out.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except groq_sdk.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="AI provider rate limit exceeded.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(exc)}") from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' or chunk '{chunk_id}' not found.",
        )

    return result


# ---------------------------------------------------------------------------
# Phase 6: CDTM Evaluation Engine Endpoints
# ---------------------------------------------------------------------------

class GroundingEvaluationRequest(BaseModel):
    answer: str = Field(..., description="Generated answer text to evaluate")
    cited_chunk_ids: list[str] = Field(
        default_factory=list,
        description="List of chunk IDs cited in the answer",
    )
    insufficient_evidence: bool = Field(
        default=False,
        description="Whether the answer indicates explicit abstention due to insufficient evidence",
    )


@router.get("/documents/{document_id}/evaluation")
async def get_document_evaluation(
    document_id: str,
    demo: bool = Query(default=False, description="Trigger controlled demonstration mode"),
):
    """
    Returns the latest available multidimensional CDTM evaluation report
    across the five independent dimensions for the document.
    """
    is_demo = bool(demo.default) if hasattr(demo, "default") else bool(demo)
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    service = get_qa_service()
    provider = service._ai_provider
    if provider is None:
        try:
            provider = service.get_provider()
        except RuntimeError:
            provider = None

    engine = CDTMEvaluationEngine(ai_provider=provider)
    return await engine.generate_document_report(document_id=document_id, demo=is_demo)


@router.post("/documents/{document_id}/evaluation/grounding")
async def evaluate_document_grounding(
    document_id: str,
    request: GroundingEvaluationRequest,
    demo: bool = Query(default=False, description="Trigger controlled demonstration mode"),
):
    """
    Evaluates claim-level Evidence Grounding for a generated answer against
    the actual cited passages in the document store.
    """
    is_demo = bool(demo.default) if hasattr(demo, "default") else bool(demo)
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    service = get_qa_service()
    provider = service._ai_provider
    if provider is None:
        try:
            provider = service.get_provider()
        except RuntimeError:
            provider = None

    evaluator = EvidenceGroundingEvaluator(ai_provider=provider)
    try:
        return await evaluator.evaluate_grounding(
            document_id=document_id,
            answer=request.answer,
            cited_chunk_ids=request.cited_chunk_ids,
            insufficient_evidence=request.insufficient_evidence,
            demo=is_demo,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider request timed out.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except groq_sdk.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="AI provider rate limit exceeded.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(exc)}") from exc


# ---------------------------------------------------------------------------
# Phase 7: Research Demonstration Failure Evaluation Endpoint
# ---------------------------------------------------------------------------

class DemoFailureRequest(BaseModel):
    dimension: Literal[
        "source_fidelity",
        "semantic_fidelity",
        "evidence_grounding",
        "cross_lingual_fidelity",
        "accessibility",
    ] = Field(..., description="Target dimension identifier for failure demonstration")
    document_id: str | None = Field(
        default=None,
        description="Document ID (required for grounding, semantic, and cross-lingual demos)",
    )


@router.post("/demo/evaluate-failure")
async def evaluate_failure_demo(request: DemoFailureRequest):
    """
    Controlled failure demonstration endpoint (Phase 7).
    Executes actual Phase 6 evaluators on deliberate failure fixtures.
    Does not mutate stored documents or force detection status.
    """
    dim = request.dimension
    service = get_qa_service()
    provider = service._ai_provider
    if provider is None:
        try:
            provider = service.get_provider()
        except RuntimeError:
            provider = None

    if dim == "source_fidelity":
        result = run_source_fidelity_demo()
        detection_observed = result.status in ("requires_review", "potential_issue")
        summary = (
            "Image-only page was successfully flagged as requiring human review / OCR."
            if detection_observed
            else "Extraction failure was not flagged."
        )
        return {
            "dimension": dim,
            "controlled_demo": True,
            "result": result,
            "detection_observed": detection_observed,
            "summary": summary,
        }

    if dim == "accessibility":
        result = run_accessibility_demo()
        detection_observed = result.structural_barrier_flagged
        summary = (
            "Complex syntax and unexplained acronyms were successfully flagged."
            if detection_observed
            else "Structural barrier was not flagged."
        )
        return {
            "dimension": dim,
            "controlled_demo": True,
            "result": result,
            "detection_observed": detection_observed,
            "summary": summary,
        }

    # The remaining dimensions require document_id
    if not request.document_id:
        raise HTTPException(
            status_code=400,
            detail=f"Field 'document_id' is required for '{dim}' demonstration.",
        )

    doc = get_document(request.document_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.document_id}' not found.",
        )

    chunks = doc.get("chunks", [])
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="Document has no chunks available for demonstration.",
        )

    first_chunk_id = chunks[0]["chunk_id"]

    try:
        if dim == "evidence_grounding":
            evaluator = EvidenceGroundingEvaluator(ai_provider=provider)
            res_grounding = await run_evidence_grounding_demo(request.document_id, evaluator)
            detection_observed = res_grounding.status in ("ungrounded", "partially_grounded")
            summary = (
                "Unsupported cash benefit claim was detected as ungrounded."
                if detection_observed
                else "Unsupported claim was not flagged."
            )
            return {
                "dimension": dim,
                "controlled_demo": True,
                "result": res_grounding,
                "detection_observed": detection_observed,
                "summary": summary,
            }

        if dim == "semantic_fidelity":
            simp_service = SimplificationService(ai_provider=provider)
            res_simplification = await run_semantic_fidelity_demo(
                request.document_id, first_chunk_id, simp_service
            )
            detection_observed = (
                res_simplification.fidelity.status in ("potential_issue", "requires_human_review")
                if res_simplification
                else False
            )
            summary = (
                "Deliberate omission of 'minor children' from family definition was flagged."
                if detection_observed
                else "Omission was not flagged."
            )
            return {
                "dimension": dim,
                "controlled_demo": True,
                "result": res_simplification,
                "detection_observed": detection_observed,
                "summary": summary,
            }

        if dim == "cross_lingual_fidelity":
            trans_service = TranslationService(ai_provider=provider)
            res_translation = await run_cross_lingual_demo(
                request.document_id, first_chunk_id, trans_service
            )
            detection_observed = (
                res_translation.fidelity.status in ("potential_issue", "requires_human_review")
                or res_translation.term_preservation_status == "partial"
                if res_translation
                else False
            )
            summary = (
                "Deliberate condition inversion in Hindi was flagged."
                if detection_observed
                else "Translation divergence was not flagged."
            )
            return {
                "dimension": dim,
                "controlled_demo": True,
                "result": res_translation,
                "detection_observed": detection_observed,
                "summary": summary,
            }

    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider request timed out.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except groq_sdk.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="AI provider rate limit exceeded.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Demonstration evaluation error: {str(exc)}") from exc
