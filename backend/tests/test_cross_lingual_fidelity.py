"""
Tests for Phase 5 — Cross-Lingual Fidelity (English -> Hindi).

All tests use MockAIProvider — no real API calls.

Covers:
  - Deterministic entity extraction and numeral normalization (Western & Devanagari)
  - Term preservation check (intact, partial, requires_human_review)
  - Call 1 translation and Call 2 AI review pass
  - Input provenance ('original' vs 'simplified')
  - Reversal of conditions and missing numbers detection
  - Controlled demonstration using actual document chunk with store isolation
"""
import unittest

from app.ai.base import GroundedAnswerResponse
from app.ai.mock import MockAIProvider
from app.document.store import clear_documents, get_document, save_document
from app.evaluation.cross_lingual_fidelity import (
    CrossLingualFidelityResult,
    TranslationResponse,
)
from app.services.translation_service import (
    TranslationService,
    check_term_preservation,
    devanagari_to_western_digits,
    extract_critical_entities,
    western_to_devanagari_digits,
)


def _make_provider_for_translation(
    translated_hindi: str = "पात्र किसान परिवारों को प्रति वर्ष ₹6,000 तीन किश्तों में दिए जाते हैं।",
    review_status: str = "verified",
    preserved: list[str] | None = None,
    divergent: list[str] | None = None,
) -> MockAIProvider:
    """
    Build a MockAIProvider whose generate_grounded_answer returns:
    - Call 1 (translate): translated_hindi in answer field
    - Call 2 (review): JSON in raw_response field
    """
    call_count = [0]

    class _SequentialMock(MockAIProvider):
        async def generate_grounded_answer(self, question, passages, system_instruction=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return GroundedAnswerResponse(
                    answer=translated_hindi,
                    insufficient_evidence=False,
                    cited_chunk_ids=[],
                    model_name="mock",
                    raw_response={},
                )
            else:
                return GroundedAnswerResponse(
                    answer="",
                    insufficient_evidence=False,
                    cited_chunk_ids=[],
                    model_name="mock",
                    raw_response={
                        "status": review_status,
                        "preserved_terms": preserved or ["₹6,000", "three instalments"],
                        "potentially_divergent": divergent or [],
                    },
                )

    return _SequentialMock()


_SOURCE_PASSAGE = (
    "A landholder farmer family is defined as husband, wife and minor children "
    "who own cultivable land as per land records of the state/UT. "
    "Under PM-KISAN, annual income support of Rs 6,000 is paid in three instalments of Rs 2,000. "
    "Serving government employees are excluded."
)


class TestNumeralAndTermNormalization(unittest.TestCase):
    """Unit tests for deterministic normalization and entity matching."""

    def test_digit_conversions(self):
        self.assertEqual(devanagari_to_western_digits("६,०००"), "6,000")
        self.assertEqual(devanagari_to_western_digits("१२३४५६७८९०"), "1234567890")
        self.assertEqual(western_to_devanagari_digits("6,000"), "६,०००")

    def test_extract_critical_entities(self):
        entities = extract_critical_entities(_SOURCE_PASSAGE)
        # Should extract amounts, standalone numbers, and known terms
        self.assertTrue(any("6,000" in e for e in entities))
        self.assertTrue(any("2,000" in e for e in entities))
        self.assertTrue(any("PM-KISAN" in e for e in entities))
        self.assertTrue(any("minor children" in e for e in entities))

    def test_check_term_preservation_intact_western(self):
        hindi = (
            "पीएम-किसान (PM-KISAN) के तहत, किसान परिवार को भूमि रिकॉर्ड के अनुसार "
            "प्रति वर्ष Rs 6,000 का लाभ Rs 2,000 की तीन किश्तों में दिया जाता है। "
            "नाबालिग बच्चे इसमें शामिल हैं।"
        )
        status, preserved, missing = check_term_preservation(_SOURCE_PASSAGE, hindi)
        self.assertEqual(status, "intact")
        self.assertEqual(missing, [])

    def test_check_term_preservation_intact_devanagari_numerals(self):
        hindi = (
            "पीएम-किसान योजना के अंतर्गत पात्र परिवार को ₹६,००० की सहायता "
            "₹२,००० की किश्तों में दी जाती है। नाबालिग बच्चे और भू-अभिलेख मान्य हैं।"
        )
        status, preserved, missing = check_term_preservation(_SOURCE_PASSAGE, hindi)
        self.assertEqual(status, "intact")
        self.assertEqual(missing, [])

    def test_check_term_preservation_partial_when_amount_missing(self):
        # Omit the 2,000 figure
        hindi = "किसान परिवार को ₹६,००० मिलते हैं।"
        status, preserved, missing = check_term_preservation(_SOURCE_PASSAGE, hindi)
        self.assertEqual(status, "partial")
        self.assertTrue(len(missing) > 0)

    def test_check_term_preservation_requires_review_on_empty(self):
        status, preserved, missing = check_term_preservation("Hello world.", "नमस्ते दुनिया।")
        self.assertEqual(status, "requires_human_review")


class TestTranslationService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        clear_documents()
        self.doc_id = "test-doc-translate"
        self.chunk_id = f"{self.doc_id}-p0001-c001"
        chunks = [
            {
                "chunk_id": self.chunk_id,
                "document_id": self.doc_id,
                "page_number": 1,
                "chunk_index": 1,
                "text": _SOURCE_PASSAGE,
                "source_type": "pdf_extraction",
            }
        ]
        save_document(self.doc_id, "test.pdf", chunks)

    def tearDown(self):
        clear_documents()

    async def test_successful_translation_verified(self):
        """Call 1 translates; Call 2 confirms fidelity -> verified status."""
        hindi_text = (
            "पीएम-किसान के तहत पात्र किसान परिवार को भू-अभिलेख के आधार पर प्रति वर्ष Rs 6,000 "
            "की वित्तीय सहायता Rs 2,000 की तीन किश्तों में दी जाती है। "
            "सरकारी कर्मचारी इसके लिए पात्र नहीं हैं। नाबालिग बच्चे परिवार की परिभाषा में शामिल हैं।"
        )
        provider = _make_provider_for_translation(
            translated_hindi=hindi_text,
            review_status="verified",
            preserved=["Rs 6,000", "Rs 2,000", "government employees excluded"],
        )
        service = TranslationService(ai_provider=provider)
        res = await service.translate_chunk(self.doc_id, self.chunk_id)

        self.assertIsInstance(res, TranslationResponse)
        self.assertEqual(res.chunk_id, self.chunk_id)
        self.assertEqual(res.target_language, "hi")
        self.assertEqual(res.input_variant, "original")
        self.assertEqual(res.term_preservation_status, "intact")
        self.assertEqual(res.fidelity.status, "verified")
        self.assertFalse(res.controlled_demo)

    async def test_translation_with_simplified_variant(self):
        """Input provenance is recorded as 'simplified' when translating simplified text."""
        simplified_input = "Eligible farmers get Rs 6,000 every year in three parts."
        provider = _make_provider_for_translation(
            translated_hindi="पात्र किसानों को हर साल तीन भागों में Rs 6,000 मिलते हैं।",
            review_status="verified",
        )
        service = TranslationService(ai_provider=provider)
        res = await service.translate_chunk(
            self.doc_id,
            self.chunk_id,
            input_variant="simplified",
            simplified_text=simplified_input,
        )

        self.assertEqual(res.input_variant, "simplified")
        self.assertEqual(res.source_english, simplified_input)
        self.assertEqual(res.fidelity.status, "verified")

    async def test_reversed_condition_detected_by_reviewer(self):
        """Call 2 AI review pass detects condition reversal (exclusion -> inclusion)."""
        provider = _make_provider_for_translation(
            translated_hindi="सरकारी कर्मचारी भी इसके लिए पात्र हैं।",
            review_status="potential_issue",
            divergent=["Exclusion inverted: English excludes government employees, Hindi says eligible."],
        )
        service = TranslationService(ai_provider=provider)
        res = await service.translate_chunk(self.doc_id, self.chunk_id)

        self.assertEqual(res.fidelity.status, "potential_issue")
        self.assertTrue(len(res.fidelity.potentially_divergent) > 0)
        self.assertIn("Exclusion inverted", res.fidelity.potentially_divergent[0])

    async def test_reviewer_failure_fallback_to_human_review(self):
        """If Call 2 raises an exception, fidelity defaults to requires_human_review."""
        call_count = [0]

        class _BrokenReviewer(MockAIProvider):
            async def generate_grounded_answer(self, question, passages, system_instruction=None):
                call_count[0] += 1
                if call_count[0] == 1:
                    return GroundedAnswerResponse(
                        answer="अनुवादित हिंदी पाठ।",
                        insufficient_evidence=False,
                        cited_chunk_ids=[],
                        model_name="mock",
                        raw_response={},
                    )
                raise RuntimeError("Reviewer LLM service unavailable")

        service = TranslationService(ai_provider=_BrokenReviewer())
        res = await service.translate_chunk(self.doc_id, self.chunk_id)

        self.assertEqual(res.fidelity.status, "requires_human_review")
        self.assertTrue(any("error" in d.lower() for d in res.fidelity.potentially_divergent))

    async def test_controlled_demo_alters_translation_and_retains_store_isolation(self):
        """
        demo=True creates a controlled divergence on the actual chunk, runs it
        through real evaluators, sets controlled_demo=True, and does NOT alter store.
        """
        clean_hindi = "सरकारी कर्मचारी इसके लिए पात्र नहीं हैं। सहायता Rs 6,000 है।"
        provider = _make_provider_for_translation(
            translated_hindi=clean_hindi,
            review_status="potential_issue",
            divergent=["Controlled failure: exclusion inverted."],
        )
        service = TranslationService(ai_provider=provider)
        res = await service.translate_chunk(self.doc_id, self.chunk_id, demo=True)

        self.assertTrue(res.controlled_demo)
        # Translation was deliberately altered from clean_hindi
        self.assertNotEqual(res.translated_hindi, clean_hindi)

        # In-memory store was NOT modified
        stored_doc = get_document(self.doc_id)
        self.assertEqual(stored_doc["chunks"][0]["text"], _SOURCE_PASSAGE)

    async def test_missing_document_returns_none(self):
        service = TranslationService(ai_provider=MockAIProvider())
        res = await service.translate_chunk("missing-doc-id", self.chunk_id)
        self.assertIsNone(res)

    async def test_missing_chunk_returns_none(self):
        service = TranslationService(ai_provider=MockAIProvider())
        res = await service.translate_chunk(self.doc_id, "missing-chunk-id")
        self.assertIsNone(res)

    async def test_simplify_hindi_success(self):
        """Phase 5: simplify_hindi returns valid simplified Hindi and entity checks."""
        formal_hindi = "पात्र किसान परिवारों को प्रति वर्ष ₹6,000 की वित्तीय सहायता ₹2,000 की तीन किस्तों में दी जाती है।"
        provider = _make_provider_for_translation(
            translated_hindi="किसान परिवारों को हर साल ₹6,000 तीन किश्तों में सीधे मिलते हैं।",
        )
        service = TranslationService(ai_provider=provider)
        res = await service.simplify_hindi(self.doc_id, self.chunk_id, formal_hindi)
        self.assertIsNotNone(res)
        self.assertEqual(res.chunk_id, self.chunk_id)
        self.assertEqual(res.formal_hindi, formal_hindi)
        self.assertTrue(len(res.simplified_hindi) > 0)
        self.assertIn(res.term_preservation_status, ("intact", "partial", "requires_human_review"))


class TestCrossLingualFidelitySchema(unittest.TestCase):
    """Schema checks guaranteeing user adjustments are enforced."""

    def test_controlled_demo_not_in_fidelity_result(self):
        """Adjustment 1: controlled_demo must not exist inside CrossLingualFidelityResult."""
        result = CrossLingualFidelityResult(status="verified")
        self.assertFalse(hasattr(result, "controlled_demo"))

    def test_term_preservation_status_valid_values(self):
        """Adjustment 2: term_preservation_status limited to intact, partial, requires_human_review."""
        fidelity = CrossLingualFidelityResult(status="verified")
        for val in ("intact", "partial", "requires_human_review"):
            res = TranslationResponse(
                chunk_id="c1",
                source_english="English text",
                translated_hindi="हिंदी पाठ",
                term_preservation_status=val,  # type: ignore[arg-type]
                fidelity=fidelity,
                input_variant="original",
            )
            self.assertEqual(res.term_preservation_status, val)

    def test_note_disclaimer_emphasizes_ai_review_pass(self):
        """Adjustment 4: disclaimer explicitly states Call 2 is a separate AI review pass."""
        result = CrossLingualFidelityResult(status="verified")
        self.assertIn("review pass", result.note.lower())
        self.assertIn("human", result.note.lower())


if __name__ == "__main__":
    unittest.main()
