import unittest

from app.retrieval.bm25 import BM25Okapi, BM25Retriever, tokenize


class TestBM25Tokenizer(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize(None), [])

    def test_alphanumeric_and_casing(self):
        tokens = tokenize("PM-KISAN Scheme 2020: Guidelines & Eligibility.")
        expected = ["pm-kisan", "scheme", "2020", "guidelines", "eligibility"]
        self.assertEqual(tokens, expected)

    def test_hyphenated_terms(self):
        tokens = tokenize("aadhaar-linked direct-benefit-transfer")
        self.assertEqual(tokens, ["aadhaar-linked", "direct-benefit-transfer"])


class TestBM25Okapi(unittest.TestCase):
    def test_empty_corpus(self):
        bm25 = BM25Okapi([])
        scores = bm25.get_scores(["pm-kisan"])
        self.assertEqual(scores, [])

    def test_relevance_ranking(self):
        corpus = [
            ["pm-kisan", "financial", "benefit", "farmers"],
            ["ration", "card", "pds", "food", "distribution"],
            ["farmers", "eligibility", "landholding", "pm-kisan"]
        ]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(["pm-kisan", "benefit"])

        # Document 0 has both 'pm-kisan' and 'benefit', so it should have highest score
        self.assertGreater(scores[0], scores[1])
        self.assertGreater(scores[0], scores[2])
        self.assertEqual(scores[1], 0.0)


class TestBM25Retriever(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            {
                "chunk_id": "doc123-p0001-c001",
                "document_id": "doc123",
                "page_number": 1,
                "chunk_index": 1,
                "text": "The PM-KISAN scheme provides income support to landholding farmer families.",
                "source_type": "pdf_extraction"
            },
            {
                "chunk_id": "doc123-p0002-c001",
                "document_id": "doc123",
                "page_number": 2,
                "chunk_index": 1,
                "text": "Exclusion criteria include institutional landholders and constitutional post holders.",
                "source_type": "pdf_extraction"
            },
            {
                "chunk_id": "doc123-p0002-c002",
                "document_id": "doc123",
                "page_number": 2,
                "chunk_index": 2,
                "text": "Payment is transferred directly into Aadhaar-linked bank accounts via DBT.",
                "source_type": "pdf_extraction"
            }
        ]
        self.retriever = BM25Retriever(self.chunks)

    def test_search_relevant_query(self):
        results = self.retriever.search("income support farmer", top_k=2)
        self.assertEqual(len(results), 1)
        top = results[0]
        self.assertEqual(top["chunk_id"], "doc123-p0001-c001")
        self.assertEqual(top["document_id"], "doc123")
        self.assertEqual(top["page_number"], 1)
        self.assertIn("PM-KISAN", top["text"])
        self.assertGreater(top["score"], 0.0)

    def test_search_page_attribution(self):
        results = self.retriever.search("Aadhaar bank accounts", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["page_number"], 2)
        self.assertEqual(results[0]["chunk_id"], "doc123-p0002-c002")

    def test_search_empty_query(self):
        self.assertEqual(self.retriever.search(""), [])
        self.assertEqual(self.retriever.search("   "), [])

    def test_search_no_matching_terms(self):
        results = self.retriever.search("completelyunrelatedtermxyz")
        self.assertEqual(results, [])

    def test_search_empty_corpus(self):
        retriever = BM25Retriever([])
        self.assertEqual(retriever.search("test query"), [])

    def test_search_respects_top_k(self):
        # Query matching multiple chunks
        retriever = BM25Retriever(self.chunks)
        results = retriever.search("landholders farmer accounts", top_k=1)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
