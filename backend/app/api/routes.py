from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.document.pdf_extractor import extract_pdf
from app.document.store import save_document, search_document

router = APIRouter(prefix="/api", tags=["documents"])


class SearchRequest(BaseModel):
    query: str = Field(default="", description="Search query string")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of chunks to return")
    document_id: str | None = Field(default=None, description="Document ID (optional when in URL path)")


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
