from io import BytesIO
import fitz

def extract_pdf(pdf_bytes: bytes) -> dict:
    pages = []
    warnings = []
    with fitz.open(stream=BytesIO(pdf_bytes), filetype="pdf") as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            pages.append({"page_number": page_number, "text": text})
            if not text:
                warnings.append(f"Page {page_number} has no selectable text; OCR may be required.")
        return {"page_count": len(doc), "pages": pages, "warnings": warnings}
