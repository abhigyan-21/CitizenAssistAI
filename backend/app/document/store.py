from threading import RLock
from typing import Any

from app.retrieval.bm25 import BM25Retriever

_documents: dict[str, dict[str, Any]] = {}
_lock = RLock()


def save_document(
    document_id: str,
    filename: str,
    chunks: list[dict]
) -> None:
    """Store a document's extracted chunks and initialize its BM25 retriever."""
    retriever = BM25Retriever(chunks)
    with _lock:
        _documents[document_id] = {
            "filename": filename,
            "chunks": chunks,
            "retriever": retriever
        }


def get_document(document_id: str) -> dict[str, Any] | None:
    """Return a stored document, or None if it does not exist."""
    with _lock:
        return _documents.get(document_id)


def search_document(
    document_id: str,
    query: str,
    top_k: int = 5
) -> list[dict] | None:
    """
    Search chunks for a stored document using BM25.
    Returns None if document_id is not found, or a list of ranked chunk results.
    """
    with _lock:
        doc = _documents.get(document_id)
        if doc is None:
            return None
        retriever: BM25Retriever = doc["retriever"]

    return retriever.search(query=query, top_k=top_k)


def clear_documents() -> None:
    """Clear all stored documents (primarily for test isolation)."""
    with _lock:
        _documents.clear()
