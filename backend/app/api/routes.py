from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

import groq as groq_sdk

from app.core.config import settings
from app.document.pdf_extractor import extract_pdf
from app.document.store import save_document, search_document
from app.services.qa_service import QAService

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
        chunks=result["chunks"]
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
            detail=f"Document '{document_id}' not found."
        )

    return {
        "document_id": document_id,
        "query": request.query,
        "total_results": len(results),
        "results": results
    }


@router.post("/documents/search")
async def search_document_body(request: SearchRequest):
    if not request.document_id:
        raise HTTPException(
            status_code=400,
            detail="Field 'document_id' is required when searching via this endpoint."
        )
    return await search_document_by_id(request.document_id, request)


@router.post("/documents/{document_id}/ask")
async def ask_document(document_id: str, request: AskRequest):
    """
    Evidence-grounded Question Answering endpoint (Milestone 5).
    Retrieves BM25 passages, queries Gemini, validates citations, and returns grounded answer.
    """
    question = request.get_question()
    if not question:
        raise HTTPException(
            status_code=422,
            detail="The inquiry question cannot be empty."
        )

    try:
        service = get_qa_service()
        response = await service.answer_question(
            document_id=document_id,
            question=question,
            top_k=request.top_k,
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
                detail="Gemini API rate limit or quota exceeded. Please wait a moment before trying again."
            ) from exc
        raise HTTPException(status_code=502, detail=f"AI provider error: {err_msg}") from exc

    if response is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found."
        )

    return response
