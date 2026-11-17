"""
Tests for Phase 6 — CDTM Evaluation Engine and All Five Dimensions.

Covers:
  1. Source Fidelity (Dimension a): clean extraction without reference (not_evaluated),
     image-only pages (requires_review), reference match (verified).
  2. Semantic Fidelity (Dimension b): schema integration and status handling.
  3. Evidence Grounding (Dimension c): claim-level AI review, valid vs invalid
     chunk IDs, abstention, unsupported claims.
  4. Cross-Lingual Fidelity (Dimension d): schema integration and status handling.
  5. Citizen Accessibility (Dimension e): English Flesch formulas, Hindi structural checks,
     unexplained acronyms (DBT, UT, KCC), Aadhaar contextual check, status invariant.
  6. CDTMEvaluationEngine: 5 independent dimensions, missing inputs default to
     not_evaluated, strict absence of aggregate/composite trust scores.
  7. Controlled failure demonstrations: actual evaluator execution, no forced status,
     isolation from store.
"""
import unittest

from app.ai.base import GroundedAnswerResponse
from app.ai.mock import MockAIProvider
from app.document.store import clear_documents, get_document, save_document
from app.evaluation.accessibility import (
    CitizenAccessibilityResult,
    compute_english_readability,
    evaluate_accessibility,
    find_unexplained_terms,
)
from app.evaluation.demo_failures import (
    run_accessibility_demo,
    run_evidence_grounding_demo,
    run_source_fidelity_demo,
)
from app.evaluation.engine import (
    CDTMReport,
    CDTMEvaluationEngine,
)
from app.evaluation.evidence_grounding import (
    EvidenceGroundingEvaluator,
    EvidenceGroundingResult,
)
from app.evaluation.semantic_fidelity import SemanticFidelityResult
from app.evaluation.source_fidelity import (
    SourceFidelityResult,
    evaluate_source_fidelity,
)


class TestSourceFidelityEvaluator(unittest.TestCase):
    """Tests for Dimension a: Source Fidelity."""

    def test_clean_extraction_without_reference_is_not_evaluated(self):
        """
        Safeguard 1: Selectable text and absence of warnings do NOT prove faithful extraction.
        Without reference comparison, status must remain 'not_evaluated'.
        """
        clean_extraction = {
            "page_count": 3,
            "pages": [
                {"page_number": 1, "text": "Page one selectable text."},
                {"page_number": 2, "text": "Page two selectable text."},
                {"page_number": 3, "text": "Page three selectable text."},
            ],
            "warnings": [],
        }
        res = evaluate_source_fidelity(clean_extraction)
        self.assertEqual(res.status, "not_evaluated")
        self.assertEqual(res.pages_with_text, 3)
        self.assertEqual(res.pages_without_text, 0)
        self.assertFalse(res.has_reference_comparison)
        self.assertIn("not_evaluated", res.note)

    def test_image_only_pages_yield_requires_review(self):
        """Pages with zero selectable text or warnings -> requires_review."""
        image_extraction = {
            "page_count": 2,
            "pages": [
                {"page_number": 1, "text": "Page one text."},
                {"page_number": 2, "text": ""},  # Scanned image
            ],
            "warnings": ["Page 2 has no selectable text; OCR may be required."],
        }
        res = evaluate_source_fidelity(image_extraction)
        self.assertEqual(res.status, "requires_review")
        self.assertEqual(res.pages_without_text, 1)
        self.assertTrue(len(res.warnings) > 0)

    def test_reference_comparison_match_yields_verified(self):
        """Extraction verified only when explicitly matched against trusted reference."""
        extraction = {
            "page_count": 1,
            "pages": [{"page_number": 1, "text": "Official operational guidelines for DBT scheme."}],
            "warnings": [],
        }
        ref = "Official operational guidelines for DBT scheme."
        res = evaluate_source_fidelity(extraction, reference_text=ref)
        self.assertEqual(res.status, "verified")
        self.assertTrue(res.has_reference_comparison)
        self.assertTrue(res.reference_match)

    def test_reference_comparison_mismatch_yields_requires_review(self):
        """Mismatch against trusted reference flags requires_review."""
        extraction = {
            "page_count": 1,
            "pages": [{"page_number": 1, "text": "Corrupted or altered text extracted."}],
            "warnings": [],
        }
        ref = "Official operational guidelines for DBT scheme."
        res = evaluate_source_fidelity(extraction, reference_text=ref)
        self.assertEqual(res.status, "requires_review")
        self.assertFalse(res.reference_match)


class TestEvidenceGroundingEvaluator(unittest.IsolatedAsyncioTestCase):
    """Tests for Dimension c: Evidence Grounding."""

    def setUp(self):
        clear_documents()
        self.doc_id = "grounding-doc"
        self.chunk_id = f"{self.doc_id}-p0001-c001"
        chunks = [
            {
                "chunk_id": self.chunk_id,
                "document_id": self.doc_id,
                "page_number": 1,
                "chunk_index": 1,
                "text": "Beneficiaries receive Rs 6,000 annually. Landholding criteria apply.",
                "source_type": "pdf_extraction",
            }
        ]
        save_document(self.doc_id, "test.pdf", chunks)

    def tearDown(self):
        clear_documents()

    async def test_fully_grounded_answer(self):
        """When AI claim review corroborates all claims against cited chunks -> grounded."""
        target_chunk_id = self.chunk_id

        class _CorroboratingMock(MockAIProvider):
            async def generate_grounded_answer(self, question, passages, system_instruction=None):
                return GroundedAnswerResponse(
                    answer="",
                    insufficient_evidence=False,
                    cited_chunk_ids=[],
                    model_name="mock",
                    raw_response={
                        "claims": [
                            {
                                "claim": "Beneficiaries receive Rs 6,000 annually.",
                                "supported": True,
                                "citing_chunk_ids": [target_chunk_id],
                                "reasoning": "Directly matches chunk text.",
                            }
                        ]
                    },
                )

        evaluator = EvidenceGroundingEvaluator(ai_provider=_CorroboratingMock())
        res = await evaluator.evaluate_grounding(
            document_id=self.doc_id,
            answer="Beneficiaries receive Rs 6,000 annually.",
            cited_chunk_ids=[self.chunk_id],
        )

        self.assertEqual(res.status, "grounded")
        self.assertEqual(res.valid_chunk_ids, [self.chunk_id])
        self.assertEqual(res.supported_claims_count, 1)
        self.assertEqual(res.unsupported_claims_count, 0)

    async def test_unsupported_claim_detected(self):
        """
        Safeguard 3: Valid citation IDs alone do not prove claims are supported.
        AI claim auditor flags an unsupported statement -> partially_grounded or ungrounded.
        """
        target_chunk_id = self.chunk_id

        class _UnsupportedMock(MockAIProvider):
            async def generate_grounded_answer(self, question, passages, system_instruction=None):
                return GroundedAnswerResponse(
                    answer="",
                    insufficient_evidence=False,
                    cited_chunk_ids=[],
                    model_name="mock",
                    raw_response={
                        "claims": [
                            {
                                "claim": "Beneficiaries receive Rs 6,000.",
                                "supported": True,
                                "citing_chunk_ids": [target_chunk_id],
                            },
                            {
                                "claim": "All citizens get free tractors.",
                                "supported": False,
                                "citing_chunk_ids": [],
                                "reasoning": "Not stated anywhere in passage.",
                            },
                        ]
                    },
                )

        evaluator = EvidenceGroundingEvaluator(ai_provider=_UnsupportedMock())
        res = await evaluator.evaluate_grounding(
            document_id=self.doc_id,
            answer="Beneficiaries receive Rs 6,000. All citizens get free tractors.",
            cited_chunk_ids=[self.chunk_id],
        )

        self.assertEqual(res.status, "partially_grounded")
        self.assertEqual(res.supported_claims_count, 1)
        self.assertEqual(res.unsupported_claims_count, 1)

    async def test_fabricated_citation_id_yields_ungrounded(self):
        """Citations not in requested document store are rejected."""
        evaluator = EvidenceGroundingEvaluator(ai_provider=MockAIProvider())
        res = await evaluator.evaluate_grounding(
            document_id=self.doc_id,
            answer="Beneficiaries receive Rs 6,000.",
            cited_chunk_ids=["nonexistent-chunk-999"],
        )
        self.assertEqual(res.status, "ungrounded")
        self.assertIn("nonexistent-chunk-999", res.invalid_chunk_ids)

    async def test_explicit_abstention_recognized(self):
        """When insufficient_evidence is indicated, status is abstained."""
        evaluator = EvidenceGroundingEvaluator(ai_provider=MockAIProvider())
        res = await evaluator.evaluate_grounding(
            document_id=self.doc_id,
            answer="The document does not contain verifiable evidence for this inquiry.",
            cited_chunk_ids=[],
            insufficient_evidence=True,
        )
        self.assertEqual(res.status, "abstained")


class TestCitizenAccessibilityEvaluator(unittest.TestCase):
    """Tests for Dimension e: Citizen Accessibility."""

    def test_flesch_reading_ease_english_only(self):
        """English text computes standard Flesch Reading Ease & Grade Level."""
        text = "This is a simple sentence. We can read it easily."
        fre, fkgl, cat = compute_english_readability(text)
        self.assertIsInstance(fre, float)
        self.assertIsInstance(fkgl, float)
        self.assertGreater(fre, 60.0)  # Plain/easy

    def test_hindi_text_does_not_apply_english_flesch(self):
        """
        Safeguard 2: Never apply English readability formulas to Hindi text.
        Flesch scores must be None for Hindi.
        """
        hindi_text = "किसान क्रेडिट कार्ड के माध्यम से किसानों को वित्तीय सहायता दी जाती है।"
        res = evaluate_accessibility(text=hindi_text, language="hi")
        self.assertIsNone(res.proxy_metrics.flesch_reading_ease)
        self.assertIsNone(res.proxy_metrics.flesch_kincaid_grade)
        self.assertEqual(res.proxy_metrics.language, "hi")

    def test_unexplained_acronyms_detected(self):
        """Unexplained bureaucratic acronyms (DBT, UT, KCC) are flagged."""
        text = "Beneficiaries in the UT will receive disbursements via DBT using KCC."
        unexplained_acrs, _ = find_unexplained_terms(text)
        self.assertIn("DBT", unexplained_acrs)
        self.assertIn("UT", unexplained_acrs)
        self.assertIn("KCC", unexplained_acrs)

    def test_explained_acronym_not_flagged(self):
        """When an acronym is accompanied by its expansion, it is not flagged."""
        text = "Disbursements via DBT [Direct Benefit Transfer] are processed."
        unexplained_acrs, _ = find_unexplained_terms(text)
        self.assertNotIn("DBT", unexplained_acrs)

    def test_aadhaar_contextual_explanation(self):
        """
        Safeguard 2: Aadhaar is treated as an administrative term requiring
        contextual explanation, not an acronym.
        """
        unexplained = "Please link your Aadhaar immediately."
        _, terms_flagged = find_unexplained_terms(unexplained)
        self.assertTrue(any("Aadhaar" in t for t in terms_flagged))

        explained = "Please link your Aadhaar [12-digit national ID] immediately."
        _, terms_clean = find_unexplained_terms(explained)
        self.assertEqual(terms_clean, [])

    def test_citizen_accessibility_status_invariant(self):
        """
        Safeguard 2: Actual Citizen Accessibility status strictly remains
        'not_evaluated' until validated by empirical user studies.
        """
        text = "Simple plain sentence for citizens."
        res = evaluate_accessibility(text=text, language="en")
        self.assertEqual(res.status, "not_evaluated")
        self.assertIn("empirical", res.note.lower())


class TestCDTMEvaluationEngine(unittest.IsolatedAsyncioTestCase):
    """Tests for CDTMEvaluationEngine and CDTMReport."""

    def setUp(self):
        clear_documents()
        self.doc_id = "engine-doc"
        self.chunk_id = f"{self.doc_id}-p0001-c001"
        chunks = [
            {
                "chunk_id": self.chunk_id,
                "document_id": self.doc_id,
                "page_number": 1,
                "chunk_index": 1,
                "text": "The scheme pays Rs 6,000 annually to eligible farmer families.",
                "source_type": "pdf_extraction",
            }
        ]
        save_document(self.doc_id, "test.pdf", chunks)

    def tearDown(self):
        clear_documents()

    async def test_five_separate_dimensions_and_no_composite_score(self):
        """
        Safeguard 4: Engine returns five independent evaluation reports.
        Never calculates a composite, weighted score, or rank.
        """
        engine = CDTMEvaluationEngine(ai_provider=MockAIProvider())
        report = await engine.generate_document_report(document_id=self.doc_id)

        self.assertIsInstance(report, CDTMReport)
        self.assertEqual(report.document_id, self.doc_id)

        # All five dimensions present
        self.assertIsInstance(report.source_fidelity, SourceFidelityResult)
        self.assertIsInstance(report.semantic_fidelity, SemanticFidelityResult)
        self.assertIsInstance(report.evidence_grounding, EvidenceGroundingResult)
        self.assertTrue(hasattr(report, "cross_lingual_fidelity"))
        self.assertIsInstance(report.citizen_accessibility, CitizenAccessibilityResult)

        # Invariant: No aggregate or combined trust score attribute
        self.assertFalse(hasattr(report, "trust_score"))
        self.assertFalse(hasattr(report, "overall_score"))
        self.assertFalse(hasattr(report, "composite_rating"))

    async def test_unrun_inputs_default_to_not_evaluated(self):
        """Dimensions without prior execution inputs default cleanly to not_evaluated."""
        engine = CDTMEvaluationEngine(ai_provider=MockAIProvider())
        report = await engine.generate_document_report(document_id=self.doc_id)

        self.assertEqual(report.semantic_fidelity.status, "not_evaluated")
        self.assertEqual(report.evidence_grounding.status, "not_evaluated")
        self.assertEqual(report.cross_lingual_fidelity.status, "not_evaluated")
        self.assertEqual(report.citizen_accessibility.status, "not_evaluated")


class TestControlledDemonstrations(unittest.IsolatedAsyncioTestCase):
    """Tests for isolated controlled failure fixtures."""

    def test_source_fidelity_demo_detection(self):
        """Source fidelity demo with empty page is evaluated honestly as requires_review."""
        res = run_source_fidelity_demo()
        self.assertTrue(res.controlled_demo)
        self.assertEqual(res.status, "requires_review")
        self.assertEqual(res.pages_without_text, 1)

    async def test_evidence_grounding_demo_detection(self):
        """Evidence grounding demo passes unsupported claim through actual reviewer."""
        clear_documents()
        doc_id = "demo-doc"
        chunk_id = f"{doc_id}-p0001-c001"
        save_document(doc_id, "demo.pdf", [{"chunk_id": chunk_id, "document_id": doc_id, "page_number": 1, "text": "Real guideline text."}])

        class _MockDetectingUnsupported(MockAIProvider):
            async def generate_grounded_answer(self, question, passages, system_instruction=None):
                return GroundedAnswerResponse(
                    answer="",
                    insufficient_evidence=False,
                    cited_chunk_ids=[],
                    model_name="mock",
                    raw_response={
                        "claims": [
                            {
                                "claim": "All citizens receive Rs 50,000 monthly unconditional cash.",
                                "supported": False,
                                "reasoning": "Passage contains no such benefit amount.",
                            }
                        ]
                    },
                )

        evaluator = EvidenceGroundingEvaluator(ai_provider=_MockDetectingUnsupported())
        res = await run_evidence_grounding_demo(document_id=doc_id, evaluator=evaluator)

        self.assertTrue(res.controlled_demo)
        self.assertEqual(res.status, "ungrounded")
        self.assertEqual(res.unsupported_claims_count, 1)

        # Store was not mutated
        stored = get_document(doc_id)
        self.assertEqual(stored["chunks"][0]["text"], "Real guideline text.")
        clear_documents()

    def test_accessibility_demo_detection(self):
        """Accessibility demo flags low reading ease and unexplained acronyms."""
        res = run_accessibility_demo()
        self.assertTrue(res.controlled_demo)
        self.assertTrue(res.structural_barrier_flagged)
        self.assertTrue(len(res.proxy_metrics.unexplained_acronyms) > 0)
        self.assertEqual(res.status, "not_evaluated")


if __name__ == "__main__":
    unittest.main()
