from typing import Any
import logging

from app.ai.base import AIProvider
from app.ai.gemini import GeminiProvider
from app.ai.groq import GroqProvider
from app.core.config import settings
from app.document.store import get_document, search_document

logger = logging.getLogger(__name__)

_SUPPORTED_PROVIDERS = {"groq", "gemini"}


class QAService:
    """
    Service responsible for Evidence-Grounded Question Answering.
    Combines BM25 lexical retrieval with an AI Provider and validates citations.
    """

    def __init__(self, ai_provider: AIProvider | None = None) -> None:
        self._ai_provider = ai_provider

    def get_provider(self) -> AIProvider:
        """
        Resolve the active AI provider from configuration.
        Provider is selected via AI_PROVIDER env var ('groq' or 'gemini').
        No automatic fallback between providers — failures surface as errors.
        """
        if self._ai_provider is not None:
            return self._ai_provider

        selected = (settings.ai_provider or "groq").strip().lower()

        if selected not in _SUPPORTED_PROVIDERS:
            raise RuntimeError(
                f"Unknown AI_PROVIDER '{selected}'. "
                f"Supported values: {sorted(_SUPPORTED_PROVIDERS)}."
            )

        if selected == "groq":
            if not settings.groq_api_key or not settings.groq_api_key.strip():
                raise RuntimeError(
                    "GROQ_API_KEY is not configured on the backend. "
                    "Set GROQ_API_KEY in your environment to enable AI-assisted Q&A."
                )
            return GroqProvider(
                api_key=settings.groq_api_key.strip(),
                model_name=settings.groq_model,
                timeout_seconds=settings.groq_timeout_seconds,
            )

        # selected == "gemini"
        if not settings.gemini_api_key or not settings.gemini_api_key.strip():
            raise RuntimeError(
                "GEMINI_API_KEY is not configured on the backend. "
                "Set GEMINI_API_KEY in your environment to enable AI-assisted Q&A."
            )
        return GeminiProvider(
            api_key=settings.gemini_api_key.strip(),
            model_name=settings.gemini_model,
            timeout_seconds=settings.gemini_timeout_seconds,
        )

    async def answer_question(
        self,
        document_id: str,
        question: str,
        top_k: int = 5,
    ) -> dict[str, Any] | None:
        """
        Execute the end-to-end grounded question answering pipeline:
        1. Validate document presence.
        2. Retrieve relevant chunks via BM25.
        3. Invoke AI provider with strict grounding context.
        4. Validate citations against actually retrieved chunks.
        5. Return structured, verified response.
        """
        # 1. Validate document exists in store
        doc = get_document(document_id)
        if doc is None:
            return None

        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Inquiry question cannot be empty.")

        # Clamp top_k to sensible boundaries (1 to 20)
        bounded_top_k = max(1, min(top_k, 20))

        # 2. Retrieve top relevant chunks via existing BM25 implementation
        retrieved_passages = search_document(
            document_id=document_id,
            query=clean_question,
            top_k=bounded_top_k,
        ) or []

        # If zero passages retrieved or document has no text, abstain immediately
        if not retrieved_passages:
            return {
                "document_id": document_id,
                "question": clean_question,
                "answer": (
                    "The uploaded administrative document does not contain passages "
                    "relevant to this question. No verifiable evidence was found."
                ),
                "insufficient_evidence": True,
                "cited_chunk_ids": [],
                "citations": [],
                "retrieved_evidence": [],
                "provider_info": {
                    "provider": "lexical_filter",
                    "model": "bm25",
                },
            }

        # 3. Resolve AI provider
        provider = self.get_provider()

        # 4. Generate grounded response
        generation = await provider.generate_grounded_answer(
            question=clean_question,
            passages=retrieved_passages,
        )

        # 5. Backend citation validation
        # Map retrieved chunk_id -> passage
        retrieved_lookup = {
            p["chunk_id"]: p for p in retrieved_passages if "chunk_id" in p
        }

        validated_citations = []
        valid_cited_ids = []

        for cid in generation.cited_chunk_ids:
            if cid in retrieved_lookup and cid not in valid_cited_ids:
                passage = retrieved_lookup[cid]
                valid_cited_ids.append(cid)
                validated_citations.append({
                    "chunk_id": cid,
                    "document_id": document_id,
                    "filename": doc.get("filename", ""),
                    "page_number": passage.get("page_number", 1),
                    "text": passage.get("text", ""),
                })

        # Evidentiary verification check:
        # If the model did not mark insufficient_evidence, but cited ZERO valid chunks,
        # we treat this as unverified/insufficient evidence rather than presenting ungrounded text.
        insufficient = generation.insufficient_evidence
        answer_text = generation.answer

        if not insufficient and not valid_cited_ids:
            insufficient = True
            answer_text = (
                f"{answer_text}\n\n"
                "[Notice: The generated response could not be verified against the "
                "retrieved passages because no valid document citations were provided.]"
            )

        return {
            "document_id": document_id,
            "question": clean_question,
            "answer": answer_text,
            "insufficient_evidence": insufficient,
            "cited_chunk_ids": valid_cited_ids,
            "citations": validated_citations,
            "retrieved_evidence": retrieved_passages,
            "provider_info": {
                "provider": "google-gemini" if isinstance(provider, GeminiProvider) else "mock",
                "model": generation.model_name or settings.gemini_model,
            },
        }
