
from io import BytesIO
import hashlib
import re

import pymupdf



def split_into_chunks(
    text: str,
    max_chars: int = 1000,
    overlap: int = 150
) -> list[str]:
    """
    Create overlapping chunks without splitting words.
    Chunks remain restricted to their original PDF page.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")

    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be between zero and max_chars.")

    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))

        if end < len(text):
            min_boundary = start + max_chars // 2

            # Prefer a sentence boundary.
            sentence_boundary = text.rfind(". ", min_boundary, end)

            if sentence_boundary != -1:
                end = sentence_boundary + 1
            else:
                # Otherwise, use a complete word boundary.
                word_boundary = text.rfind(" ", min_boundary, end)
                if word_boundary != -1:
                    end = word_boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # Keep overlap, but move its start to a word boundary.
        next_start = max(start + 1, end - overlap)

        if not text[next_start - 1].isspace():
            next_space = text.find(" ", next_start, end)

            if next_space == -1:
                next_start = end
            else:
                next_start = next_space + 1

        start = next_start

    return chunks


def extract_pdf(pdf_bytes: bytes) -> dict:
    pages = []
    chunks = []
    warnings = []

    document_id = hashlib.sha256(pdf_bytes).hexdigest()[:16]

    with pymupdf.open(
        stream=BytesIO(pdf_bytes),
        filetype="pdf"
    ) as doc:

        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()

            pages.append({
                "page_number": page_number,
                "text": text
            })

            if not text:
                warnings.append(
                    f"Page {page_number} has no selectable text; "
                    "OCR may be required."
                )
                continue

            page_chunks = split_into_chunks(text)

            for chunk_index, chunk_text in enumerate(
                page_chunks,
                start=1
            ):
                chunks.append({
                    "chunk_id": (
                        f"{document_id}-"
                        f"p{page_number:04d}-"
                        f"c{chunk_index:03d}"
                    ),
                    "document_id": document_id,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "source_type": "pdf_extraction"
                })

    return {
        "document_id": document_id,
        "page_count": len(pages),
        "pages": pages,
        "chunks": chunks,
        "chunk_count": len(chunks),
        "warnings": warnings
    }
