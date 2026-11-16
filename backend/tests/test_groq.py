"""
Tests for Groq AI Provider integration (Milestone 6).

All tests use mocked Groq SDK clients — no real API calls are made.
Covers:
  1.  Successful Groq provider response and GroundedAnswerResponse conversion.
  2.  Valid citation handling.
  3.  Fabricated citation rejection (via QAService citation validation).
  4.  Insufficient-evidence abstention from provider.
  5.  Rate-limit error (RateLimitError → HTTP 429).
  6.  Authentication error (AuthenticationError → HTTP 503).
  7.  Timeout handling (asyncio.TimeoutError and APITimeoutError → TimeoutError).
  8.  Malformed JSON from model → abstention fallback.
  9.  Provider selection: AI_PROVIDER=groq selects GroqProvider.
  10. Provider selection: AI_PROVIDER=gemini selects GeminiProvider.
  11. Missing GROQ_API_KEY raises RuntimeError.
"""

import asyncio
import json
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import groq as groq_sdk
from fastapi import HTTPException

from app.ai.base import GroundedAnswerResponse
from app.ai.gemini import GeminiProvider
from app.ai.groq import GroqProvider
from app.ai.mock import MockAIProvider
from app.api.routes import AskRequest, ask_document, set_qa_service
from app.core.config import settings
from app.document.store import clear_documents, save_document
from app.services.qa_service import QAService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_groq_response(content: str) -> MagicMock:
    """Build a minimal mock that looks like a groq ChatCompletion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


def _valid_json_response(
    answer: str = "The benefit is Rs 6,000 per year.",
    insufficient_evidence: bool = False,
    cited_chunk_ids: list[str] | None = None,
) -> str:
    return json.dumps(
        {
            "answer": answer,
            "insufficient_evidence": insufficient_evidence,
            "cited_chunk_ids": cited_chunk_ids or [],
        }
    )


# ---------------------------------------------------------------------------
# Unit tests for GroqProvider
# ---------------------------------------------------------------------------


class TestGroqProvider(unittest.IsolatedAsyncioTestCase):
    def _make_provider(self) -> GroqProvider:
        return GroqProvider(
            api_key="test-key-not-real",
            model_name="llama-3.3-70b-versatile",
            timeout_seconds=10.0,
        )

    # -- Test 1 & 2: Successful response + GroundedAnswerResponse conversion --------

    async def test_successful_response_and_conversion(self):
        """Test 1 & 2: Valid JSON response converts to correct GroundedAnswerResponse."""
        passages = [
            {
                "chunk_id": "doc-p001-c001",
                "page_number": 1,
                "text": "The PM-KISAN scheme provides Rs 6,000 per year.",
            }
        ]
        content = _valid_json_response(
            answer="The benefit is Rs 6,000 per year.",
            insufficient_evidence=False,
            cited_chunk_ids=["doc-p001-c001"],
        )
        mock_response = _make_groq_response(content)

        provider = self._make_provider()
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.generate_grounded_answer(
            question="What is the financial benefit?",
            passages=passages,
        )

        self.assertIsInstance(result, GroundedAnswerResponse)
        self.assertIn("6,000", result.answer)
        self.assertFalse(result.insufficient_evidence)
        self.assertEqual(result.cited_chunk_ids, ["doc-p001-c001"])
        self.assertEqual(result.model_name, "llama-3.3-70b-versatile")

    # -- Test 3: Valid citation handling ------------------------------------------

    async def test_valid_citations_returned(self):
        """Test 3: Multiple valid chunk IDs are preserved in cited_chunk_ids."""
        passages = [
            {"chunk_id": "c001", "page_number": 1, "text": "Income support info."},
            {"chunk_id": "c002", "page_number": 2, "text": "Family definition."},
        ]
        content = _valid_json_response(
            answer="Answer citing two passages.",
            cited_chunk_ids=["c001", "c002"],
        )
        mock_response = _make_groq_response(content)

        provider = self._make_provider()
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.generate_grounded_answer(
            question="Tell me about income and family.",
            passages=passages,
        )

        self.assertEqual(result.cited_chunk_ids, ["c001", "c002"])
        self.assertFalse(result.insufficient_evidence)

    # -- Test 4: Fabricated citation rejection (via QAService) --------------------
    # Provider returns a fake chunk ID; QAService must strip it.

    async def test_fabricated_citation_stripped_by_qa_service(self):
        """Test 4: QAService drops chunk IDs not present in retrieved passages."""
        clear_documents()
        doc_id = "groq-test-doc"
        chunks = [
            {
                "chunk_id": "groq-test-doc-p0001-c001",
                "document_id": doc_id,
                "page_number": 1,
                "chunk_index": 1,
                "text": "Farmers receive six thousand rupees annually under PM-KISAN.",
                "source_type": "pdf_extraction",
            }
        ]
        save_document(doc_id, "groq_test.pdf", chunks)

        # Provider claims to cite a fabricated chunk that was never retrieved
        mock_provider = MockAIProvider(
            mock_answer="Some answer.",
            mock_insufficient_evidence=False,
            mock_cited_chunk_ids=["groq-test-doc-p0001-c001", "fabricated-999"],
        )
        service = QAService(ai_provider=mock_provider)

        result = await service.answer_question(
            document_id=doc_id,
            question="six thousand rupees annually",
            top_k=5,
        )

        # Fabricated ID must be stripped; only real retrieved ID survives
        self.assertNotIn("fabricated-999", result["cited_chunk_ids"])
        # Real chunk ID should be present (it was retrieved via BM25)
        self.assertIn("groq-test-doc-p0001-c001", result["cited_chunk_ids"])
        clear_documents()

    # -- Test 5: Insufficient-evidence abstention ---------------------------------

    async def test_insufficient_evidence_abstention(self):
        """Test 5: Provider signals insufficient_evidence=True → abstention preserved."""
        passages = [
            {"chunk_id": "c001", "page_number": 1, "text": "Unrelated content."},
        ]
        content = _valid_json_response(
            answer="The document does not contain relevant information.",
            insufficient_evidence=True,
            cited_chunk_ids=[],
        )
        mock_response = _make_groq_response(content)

        provider = self._make_provider()
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.generate_grounded_answer(
            question="Does it mention solar pumps?",
            passages=passages,
        )

        self.assertTrue(result.insufficient_evidence)
        self.assertEqual(result.cited_chunk_ids, [])

    # -- Test 6: Rate-limit error → re-raised as RateLimitError -------------------

    async def test_rate_limit_error_raised(self):
        """Test 6: RateLimitError from Groq SDK is re-raised (mapped to HTTP 429 by route)."""
        provider = self._make_provider()
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(
            side_effect=groq_sdk.RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429, headers={}),
                body={},
            )
        )

        with self.assertRaises(groq_sdk.RateLimitError):
            await provider.generate_grounded_answer(
                question="Any question?",
                passages=[{"chunk_id": "c1", "page_number": 1, "text": "text"}],
            )

    # -- Test 7: Authentication error → RuntimeError ------------------------------

    async def test_authentication_error_raises_runtime_error(self):
        """Test 7: AuthenticationError is converted to RuntimeError with safe message."""
        provider = self._make_provider()
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(
            side_effect=groq_sdk.AuthenticationError(
                message="Invalid API key",
                response=MagicMock(status_code=401, headers={}),
                body={},
            )
        )

        with self.assertRaises(RuntimeError) as ctx:
            await provider.generate_grounded_answer(
                question="Any question?",
                passages=[{"chunk_id": "c1", "page_number": 1, "text": "text"}],
            )
        # Key must NOT appear in the error message
        self.assertIn("authentication failed", str(ctx.exception).lower())
        self.assertNotIn("test-key-not-real", str(ctx.exception))

    # -- Test 8: Timeout handling -------------------------------------------------

    async def test_asyncio_timeout_raises_timeout_error(self):
        """Test 8a: asyncio.TimeoutError is converted to TimeoutError."""
        provider = self._make_provider()
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        # Patch wait_for to raise immediately
        with patch("app.ai.groq.asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            with self.assertRaises(TimeoutError):
                await provider.generate_grounded_answer(
                    question="Any?",
                    passages=[{"chunk_id": "c1", "page_number": 1, "text": "text"}],
                )

    async def test_sdk_api_timeout_raises_timeout_error(self):
        """Test 8b: groq.APITimeoutError is converted to TimeoutError."""
        provider = self._make_provider()
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(
            side_effect=groq_sdk.APITimeoutError(request=MagicMock())
        )

        with self.assertRaises(TimeoutError):
            await provider.generate_grounded_answer(
                question="Any?",
                passages=[{"chunk_id": "c1", "page_number": 1, "text": "text"}],
            )

    # -- Malformed JSON → abstention fallback -------------------------------------

    async def test_malformed_json_produces_abstention(self):
        """Malformed JSON from model returns insufficient_evidence=True."""
        mock_response = _make_groq_response("This is not JSON at all.")

        provider = self._make_provider()
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.generate_grounded_answer(
            question="Any question?",
            passages=[{"chunk_id": "c1", "page_number": 1, "text": "text"}],
        )

        self.assertTrue(result.insufficient_evidence)
        self.assertEqual(result.cited_chunk_ids, [])


# ---------------------------------------------------------------------------
# Provider selection tests (via QAService.get_provider)
# ---------------------------------------------------------------------------


class TestProviderSelection(unittest.TestCase):
    def tearDown(self):
        # Restore defaults after each test
        settings.ai_provider = "groq"
        settings.groq_api_key = None
        settings.gemini_api_key = None

    # -- Test 9: AI_PROVIDER=groq selects GroqProvider ---------------------------

    def test_groq_provider_selected_when_configured(self):
        """Test 9: get_provider() returns GroqProvider when AI_PROVIDER=groq."""
        settings.ai_provider = "groq"
        settings.groq_api_key = "dummy-groq-key"
        service = QAService()
        provider = service.get_provider()
        self.assertIsInstance(provider, GroqProvider)

    # -- Test 10: AI_PROVIDER=gemini selects GeminiProvider ----------------------

    def test_gemini_provider_selected_when_configured(self):
        """Test 10: get_provider() returns GeminiProvider when AI_PROVIDER=gemini."""
        settings.ai_provider = "gemini"
        settings.gemini_api_key = "dummy-gemini-key"
        service = QAService()
        provider = service.get_provider()
        self.assertIsInstance(provider, GeminiProvider)

    # -- Test 11: Missing GROQ_API_KEY raises RuntimeError -----------------------

    def test_missing_groq_api_key_raises_runtime_error(self):
        """Test 11: RuntimeError raised when GROQ_API_KEY is absent."""
        settings.ai_provider = "groq"
        settings.groq_api_key = None
        service = QAService()
        with self.assertRaises(RuntimeError) as ctx:
            service.get_provider()
        self.assertIn("GROQ_API_KEY", str(ctx.exception))

    def test_missing_gemini_api_key_raises_runtime_error(self):
        """Missing GEMINI_API_KEY with AI_PROVIDER=gemini raises RuntimeError."""
        settings.ai_provider = "gemini"
        settings.gemini_api_key = None
        service = QAService()
        with self.assertRaises(RuntimeError) as ctx:
            service.get_provider()
        self.assertIn("GEMINI_API_KEY", str(ctx.exception))

    def test_unknown_provider_raises_runtime_error(self):
        """Unknown AI_PROVIDER value raises RuntimeError."""
        settings.ai_provider = "openai"
        service = QAService()
        with self.assertRaises(RuntimeError) as ctx:
            service.get_provider()
        self.assertIn("openai", str(ctx.exception))

    # -- Injected provider bypasses selection -------------------------------------

    def test_injected_provider_bypasses_selection(self):
        """An explicitly injected provider is returned regardless of AI_PROVIDER setting."""
        settings.ai_provider = "groq"
        mock = MockAIProvider()
        service = QAService(ai_provider=mock)
        self.assertIs(service.get_provider(), mock)


# ---------------------------------------------------------------------------
# Route-level integration: Groq rate-limit → HTTP 429
# ---------------------------------------------------------------------------


class TestAskRouteGroqErrors(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        clear_documents()
        self.doc_id = "groq-route-doc"
        chunks = [
            {
                "chunk_id": "groq-route-doc-p0001-c001",
                "document_id": self.doc_id,
                "page_number": 1,
                "chunk_index": 1,
                "text": "Farmers receive six thousand rupees annually.",
                "source_type": "pdf_extraction",
            }
        ]
        save_document(self.doc_id, "groq_route.pdf", chunks)

    def tearDown(self):
        clear_documents()
        set_qa_service(QAService())

    async def test_rate_limit_returns_429(self):
        """RateLimitError from GroqProvider propagates to HTTP 429 at route level."""
        provider = MockAIProvider(
            simulate_error=groq_sdk.RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429, headers={}),
                body={},
            )
        )
        set_qa_service(QAService(ai_provider=provider))

        req = AskRequest(query="six thousand rupees annually")
        with self.assertRaises(HTTPException) as ctx:
            await ask_document(self.doc_id, req)
        self.assertEqual(ctx.exception.status_code, 429)

    async def test_auth_error_returns_503(self):
        """AuthenticationError (re-raised as RuntimeError) → HTTP 503."""
        provider = MockAIProvider(
            simulate_error=RuntimeError("Groq authentication failed. Check GROQ_API_KEY.")
        )
        set_qa_service(QAService(ai_provider=provider))

        req = AskRequest(query="six thousand rupees annually")
        with self.assertRaises(HTTPException) as ctx:
            await ask_document(self.doc_id, req)
        self.assertEqual(ctx.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
