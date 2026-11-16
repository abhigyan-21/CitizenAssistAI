from fastapi import APIRouter, File, HTTPException, UploadFile
from app.core.config import settings
from app.document.pdf_extractor import extract_pdf

router = APIRouter(prefix="/api", tags=["documents"])

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

    return {
        "filename": filename,
        **result,
        "source_fidelity_status": "requires_review" if result["warnings"] else "not_evaluated",
    }
