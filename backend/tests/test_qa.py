import unittest
from fastapi import HTTPException

from app.ai.base import GroundedAnswerResponse
from app.ai.mock import MockAIProvider
from app.api.routes import AskRequest, ask_document, set_qa_service, get_qa_service
from app.core.config import settings
from app.document.store import clear_documents, save_document
from app.services.qa_service import QAService


class TestQAService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        clear_documents()
        self.doc_id = "test-doc-001"
        self.chunks = [
            {
                "chunk_id": "test-doc-001-p0001-c001",
                "document_id": self.doc_id,
                "page_number": 1,
                "chunk_index": 1,
                "text": "The PM-KISAN scheme provides income support of Rs 6,000 per year.",
                "source_type": "pdf_extraction",
            },
            {
                "chunk_id": "test-doc-001-p0002-c001",
                "document_id": self.doc_id,
                "page_number": 2,
                "chunk_index": 1,
                "text": "A landholder farmer family is defined as husband, wife and minor children.",
                "source_type": "pdf_extraction",
            },
            {
                "chunk_id": "test-doc-001-p0003-c001",
                "document_id": self.doc_id,
                "page_number": 3,
                "chunk_index": 1,
                "text": "Exclusion list includes all serving or retired officers and employees of state/central government.",
                "source_type": "pdf_extraction",
            },
        ]
        save_document(self.doc_id, "Guidelines.pdf", self.chunks)

    def tearDown(self):
        clear_documents()
        # Reset default QA service
        set_qa_service(QAService())

    async def test_successful_grounded_answer_with_citations(self):
        """Test 1 & 2: Grounded answer generation and accurate page citation mapping."""
        mock_provider = MockAIProvider(
            mock_answer="The scheme provides Rs 6,000 per year to eligible farmer families.",
            mock_insufficient_evidence=False,
            mock_cited_chunk_ids=["test-doc-001-p0001-c001"],
            mock_model_name="mock-gemini-3.8-flash",
        )
        service = QAService(ai_provider=mock_provider)

        result = await service.answer_question(
            document_id=self.doc_id,
            question="What is the financial benefit of the scheme?",
            top_k=3,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["document_id"], self.doc_id)
        self.assertFalse(result["insufficient_evidence"])
        self.assertIn("6,000", result["answer"])
        self.assertEqual(len(result["citations"]), 1)

        citation = result["citations"][0]
        self.assertEqual(citation["chunk_id"], "test-doc-001-p0001-c001")
        self.assertEqual(citation["page_number"], 1)
        self.assertEqual(citation["filename"], "Guidelines.pdf")
        self.assertIn("income support", citation["text"])

    async def test_citation_validation_filters_unretrieved_chunks(self):
        """Test 3: Reject fabricated or unretrieved chunk IDs."""
        mock_provider = MockAIProvider(
            mock_answer="Family definition includes minor children.",
            mock_insufficient_evidence=False,
            # Includes 1 valid chunk ID and 2 fabricated/unretrieved chunk IDs
            mock_cited_chunk_ids=[
                "test-doc-001-p0002-c001",
                "fabricated-chunk-id-999",
                "another-unrelated-chunk",
            ],
        )
        service = QAService(ai_provider=mock_provider)

        result = await service.answer_question(
            document_id=self.doc_id,
            question="How is a family defined?",
            top_k=3,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["cited_chunk_ids"], ["test-doc-001-p0002-c001"])
        self.assertEqual(len(result["citations"]), 1)
        self.assertEqual(result["citations"][0]["chunk_id"], "test-doc-001-p0002-c001")

    async def test_abstention_on_insufficient_evidence(self):
        """Test 4: Explicit abstention when evidence is insufficient."""
        mock_provider = MockAIProvider(
            mock_answer="The document does not specify provisions for solar pump subsidies.",
            mock_insufficient_evidence=True,
            mock_cited_chunk_ids=[],
        )
        service = QAService(ai_provider=mock_provider)

        result = await service.answer_question(
            document_id=self.doc_id,
            question="Does the document mention solar water pumps?",
            top_k=3,
        )

        self.assertIsNotNone(result)
        self.assertTrue(result["insufficient_evidence"])
        self.assertEqual(len(result["citations"]), 0)

    async def test_missing_document_returns_none(self):
        """Test 5: Non-existent document ID returns None (handled as 404 by route)."""
        service = QAService(ai_provider=MockAIProvider())
        result = await service.answer_question(
            document_id="non-existent-doc-id",
            question="Any question?",
        )
        self.assertIsNone(result)

    async def test_missing_api_key_raises_runtime_error(self):
        """Test 6: Missing Gemini API key raises RuntimeError (handled as 503 by route)."""
        original_key = settings.gemini_api_key
        try:
            settings.gemini_api_key = None
            service = QAService(ai_provider=None)
            with self.assertRaises(RuntimeError) as ctx:
                service.get_provider()
            self.assertIn("GEMINI_API_KEY is not configured", str(ctx.exception))
        finally:
            settings.gemini_api_key = original_key

    async def test_empty_question_raises_value_error(self):
        """Test 7: Empty question raises ValueError."""
        service = QAService(ai_provider=MockAIProvider())
        with self.assertRaises(ValueError):
            await service.answer_question(
                document_id=self.doc_id,
                question="   ",
            )

    async def test_provider_timeout_handled(self):
        """Test 8: Simulated provider timeout raises TimeoutError."""
        timeout_provider = MockAIProvider(simulate_timeout=True)
        service = QAService(ai_provider=timeout_provider)
        with self.assertRaises(TimeoutError):
            await service.answer_question(
                document_id=self.doc_id,
                question="What is the benefit?",
            )


class TestAskRoute(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        clear_documents()
        self.doc_id = "route-doc-001"
        chunks = [
            {
                "chunk_id": "route-doc-001-p0001-c001",
                "document_id": self.doc_id,
                "page_number": 1,
                "chunk_index": 1,
                "text": "Beneficiaries must have an Aadhaar linked bank account for income transfer.",
                "source_type": "pdf_extraction",
            }
        ]
        save_document(self.doc_id, "test.pdf", chunks)

    def tearDown(self):
        clear_documents()
        set_qa_service(QAService())

    async def test_ask_endpoint_success(self):
        mock_provider = MockAIProvider(
            mock_answer="Aadhaar linking is mandatory for payment transfer.",
            mock_insufficient_evidence=False,
            mock_cited_chunk_ids=["route-doc-001-p0001-c001"],
            mock_model_name="gemini-3.8-flash",
        )
        set_qa_service(QAService(ai_provider=mock_provider))

        req = AskRequest(query="Aadhaar bank account", top_k=2)
        res = await ask_document(self.doc_id, req)

        self.assertEqual(res["document_id"], self.doc_id)
        self.assertEqual(res["question"], "Aadhaar bank account")
        self.assertFalse(res["insufficient_evidence"])
        self.assertEqual(len(res["citations"]), 1)
        self.assertEqual(res["citations"][0]["page_number"], 1)

    async def test_ask_endpoint_404_missing_doc(self):
        set_qa_service(QAService(ai_provider=MockAIProvider()))
        req = AskRequest(query="Some question")
        with self.assertRaises(HTTPException) as ctx:
            await ask_document("unknown-id", req)
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_ask_endpoint_422_empty_query(self):
        req = AskRequest(query="   ")
        with self.assertRaises(HTTPException) as ctx:
            await ask_document(self.doc_id, req)
        self.assertEqual(ctx.exception.status_code, 422)

    async def test_ask_endpoint_504_timeout(self):
        mock_provider = MockAIProvider(simulate_timeout=True)
        set_qa_service(QAService(ai_provider=mock_provider))

        req = AskRequest(query="Aadhaar bank account")
        with self.assertRaises(HTTPException) as ctx:
            await ask_document(self.doc_id, req)
        self.assertEqual(ctx.exception.status_code, 504)


if __name__ == "__main__":
    unittest.main()
