import io
import unittest
from fastapi import HTTPException, UploadFile
import pymupdf

from app.api.routes import SearchRequest, extract_document, search_document_by_id, search_document_body
from app.document.store import clear_documents, get_document, save_document, search_document


class TestDocumentStore(unittest.TestCase):
    def setUp(self):
        clear_documents()

    def tearDown(self):
        clear_documents()

    def test_save_and_get_document(self):
        chunks = [
            {"chunk_id": "c1", "document_id": "d1", "page_number": 1, "text": "Document text"}
        ]
        save_document("d1", "test.pdf", chunks)
        doc = get_document("d1")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["filename"], "test.pdf")
        self.assertEqual(len(doc["chunks"]), 1)

    def test_search_document_not_found(self):
        result = search_document("non-existent-id", "test query")
        self.assertIsNone(result)

    def test_search_document_empty_corpus(self):
        save_document("d_empty", "empty.pdf", [])
        result = search_document("d_empty", "test query")
        self.assertEqual(result, [])


class TestAPIRoutes(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        clear_documents()

    def tearDown(self):
        clear_documents()

    def _create_sample_pdf(self, text: str = "This is a PM-KISAN welfare document.") -> bytes:
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 72), text)
        return doc.tobytes()

    async def test_extract_and_auto_store(self):
        pdf_bytes = self._create_sample_pdf("The PM-KISAN scheme provides income support to farmers.")
        upload_file = UploadFile(
            filename="guidelines.pdf",
            file=io.BytesIO(pdf_bytes),
            headers={"content-type": "application/pdf"}
        )

        response = await extract_document(upload_file)

        # 1. Verify existing response contract is preserved (backward compatibility)
        self.assertEqual(response["filename"], "guidelines.pdf")
        self.assertIn("document_id", response)
        self.assertIn("pages", response)
        self.assertIn("chunks", response)
        self.assertEqual(response["source_fidelity_status"], "not_evaluated")

        # 2. Verify document was automatically saved in store
        doc_id = response["document_id"]
        stored_doc = get_document(doc_id)
        self.assertIsNotNone(stored_doc)
        self.assertEqual(stored_doc["filename"], "guidelines.pdf")

        # 3. Verify BM25 retrieval works on the auto-saved document
        search_req = SearchRequest(query="income support", top_k=3)
        search_res = await search_document_by_id(doc_id, search_req)
        self.assertEqual(search_res["document_id"], doc_id)
        self.assertGreaterEqual(search_res["total_results"], 1)
        top_match = search_res["results"][0]
        self.assertEqual(top_match["document_id"], doc_id)
        self.assertEqual(top_match["page_number"], 1)
        self.assertIn("income support", top_match["text"].lower())

    async def test_search_missing_document(self):
        search_req = SearchRequest(query="test", top_k=5)
        with self.assertRaises(HTTPException) as ctx:
            await search_document_by_id("missing_id", search_req)
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_search_empty_query(self):
        chunks = [
            {"chunk_id": "c1", "document_id": "d1", "page_number": 1, "text": "Valid text"}
        ]
        save_document("d1", "sample.pdf", chunks)

        search_req = SearchRequest(query="   ", top_k=5)
        res = await search_document_by_id("d1", search_req)
        self.assertEqual(res["total_results"], 0)
        self.assertEqual(res["results"], [])

    async def test_search_no_extractable_text(self):
        # Empty chunks list
        save_document("d_empty", "empty.pdf", [])
        search_req = SearchRequest(query="any query", top_k=5)
        res = await search_document_by_id("d_empty", search_req)
        self.assertEqual(res["total_results"], 0)
        self.assertEqual(res["results"], [])

    async def test_search_by_body_endpoint(self):
        chunks = [
            {"chunk_id": "c1", "document_id": "d_body", "page_number": 1, "text": "Aadhaar validation process"}
        ]
        save_document("d_body", "doc.pdf", chunks)

        # Missing document_id in body
        with self.assertRaises(HTTPException) as ctx:
            await search_document_body(SearchRequest(query="Aadhaar"))
        self.assertEqual(ctx.exception.status_code, 400)

        # Provided document_id in body
        res = await search_document_body(SearchRequest(document_id="d_body", query="Aadhaar", top_k=1))
        self.assertEqual(res["total_results"], 1)
        self.assertEqual(res["results"][0]["document_id"], "d_body")


if __name__ == "__main__":
    unittest.main()
