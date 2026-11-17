"""
Tests for Phase 4 — Semantic Fidelity: SimplificationService and simplify endpoint.

All tests use MockAIProvider — no real API calls.

Test coverage:
  Existing (10 tests): service behaviour, fidelity status paths, error handling
  New (4 tests):       transformation-check unit tests (deterministic, no AI)

Thresholds under test:
  SIMILARITY_INSUFFICIENT = 0.85  (standard passages)
  SHORT_PASSAGE_REVIEW    = 0.70  (passages < 150 normalized chars)
"""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock

from app.ai.base import GroundedAnswerResponse
from app.ai.mock import MockAIProvider
from app.api.routes import AskRequest, ask_document, set_qa_service
from app.document.store import clear_documents, save_document
from app.evaluation.semantic_fidelity import SemanticFidelityResult, SimplificationResponse
from app.services.qa_service import QAService
from app.services.simplification_service import (
    SimplificationService,
    check_transformation_quality,
    SHORT_PASSAGE_THRESHOLD,
    SIMILARITY_INSUFFICIENT,
    SHORT_PASSAGE_REVIEW,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider_for_simplify(
    simplified_text: str = "The scheme gives Rs 6,000 per year.",
    review_status: str = "verified",
    preserved: list[str] | None = None,
    missing: list[str] | None = None,
) -> MockAIProvider:
    """
    Build a MockAIProvider whose generate_grounded_answer returns:
    - Call 1 (simplify): simplified_text in answer field
    - Call 2 (review): JSON in raw_response field
    """
    call_count = [0]

    class _SequentialMock(MockAIProvider):
        async def generate_grounded_answer(self, question, passages, system_instruction=None):
            call_count[0] += 1
            if call_count[0] == 1:
                # Call 1: simplification
                return GroundedAnswerResponse(
                    answer=simplified_text,
                    insufficient_evidence=False,
                    cited_chunk_ids=[],
                    model_name="mock",
                    raw_response={},
                )
            else:
                # Call 2: review — raw_response carries the parsed JSON
                return GroundedAnswerResponse(
                    answer="",
                    insufficient_evidence=False,
                    cited_chunk_ids=[],
                    model_name="mock",
                    raw_response={
                        "status": review_status,
                        "preserved_conditions": preserved or [],
                        "potentially_missing": missing or [],
                    },
                )

    return _SequentialMock()


# ---------------------------------------------------------------------------
# Source chunk used by most service tests
# ---------------------------------------------------------------------------

_STANDARD_SOURCE = (
    "A landholder farmer family is defined as husband, wife and minor children "
    "who own cultivable land as per land records of the state/UT. "
    "Annual income support of Rs 6,000 is paid in three instalments of Rs 2,000. "
    "Government employees are excluded."
)

_STANDARD_SIMPLIFIED = "Eligible farm families get Rs 6,000 a year in three parts of Rs 2,000."

# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestSimplificationService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        clear_documents()
        self.doc_id = "simplify-test-doc"
        self.chunk_id = f"{self.doc_id}-p0001-c001"
        chunks = [
            {
                "chunk_id": self.chunk_id,
                "document_id": self.doc_id,
                "page_number": 1,
                "chunk_index": 1,
                "text": _STANDARD_SOURCE,
                "source_type": "pdf_extraction",
            }
        ]
        save_document(self.doc_id, "test.pdf", chunks)

    def tearDown(self):
        clear_documents()

    # Test 1: Successful simplification with verified fidelity
    async def test_verified_simplification(self):
        """Call 1 simplifies; Call 2 returns verified status."""
        provider = _make_provider_for_simplify(
            simplified_text=_STANDARD_SIMPLIFIED,
            review_status="verified",
            preserved=["Rs 6,000", "Rs 2,000", "three instalments"],
            missing=[],
        )
        service = SimplificationService(ai_provider=provider)
        result = await service.simplify_chunk(self.doc_id, self.chunk_id)

        self.assertIsInstance(result, SimplificationResponse)
        self.assertEqual(result.chunk_id, self.chunk_id)
        self.assertIn("Rs 6,000", result.source_passage)
        self.assertEqual(result.fidelity.status, "verified")
        self.assertFalse(result.controlled_demo)

        # New fields must be present
        self.assertIn(result.simplification_quality, ("simplified", "insufficient", "requires_human_review", "error"))
        self.assertIsInstance(result.similarity_score, float)
        self.assertGreaterEqual(result.similarity_score, 0.0)
        self.assertLessEqual(result.similarity_score, 1.0)

        # Genuinely simplified text should be detectably different
        self.assertEqual(result.simplification_quality, "simplified")
        self.assertLess(result.similarity_score, SIMILARITY_INSUFFICIENT)

    # Test 2: Potential issue detected by reviewer
    async def test_potential_issue_detected(self):
        """Reviewer flags a missing condition → potential_issue status."""
        provider = _make_provider_for_simplify(
            simplified_text="Farm families get Rs 6,000 a year.",
            review_status="potential_issue",
            preserved=["Rs 6,000"],
            missing=["minor children", "government employees excluded"],
        )
        service = SimplificationService(ai_provider=provider)
        result = await service.simplify_chunk(self.doc_id, self.chunk_id)

        self.assertEqual(result.fidelity.status, "potential_issue")
        self.assertIn("minor children", result.fidelity.potentially_missing)
        self.assertIn("government employees excluded", result.fidelity.potentially_missing)
        # simplification_quality and fidelity are independent
        self.assertIn(result.simplification_quality, ("simplified", "insufficient", "requires_human_review"))

    # Test 3: Requires human review when reviewer uncertain
    async def test_requires_human_review(self):
        """Unknown/uncertain reviewer response → requires_human_review."""
        provider = _make_provider_for_simplify(review_status="requires_human_review")
        service = SimplificationService(ai_provider=provider)
        result = await service.simplify_chunk(self.doc_id, self.chunk_id)

        self.assertEqual(result.fidelity.status, "requires_human_review")
        self.assertIn(result.simplification_quality, ("simplified", "insufficient", "requires_human_review", "error"))
        self.assertIsInstance(result.similarity_score, float)

    # Test 4: Controlled demo mode
    async def test_controlled_demo_mode(self):
        """demo=True uses the fixture with known omission; result is marked controlled_demo."""
        provider = _make_provider_for_simplify(
            review_status="potential_issue",
            missing=["minor children"],
        )
        service = SimplificationService(ai_provider=provider)
        result = await service.simplify_chunk(self.doc_id, self.chunk_id, demo=True)

        self.assertTrue(result.controlled_demo)
        self.assertTrue(result.fidelity.controlled_demo)
        # Demo source always contains "minor children"
        self.assertIn("minor children", result.source_passage)
        # Demo simplified deliberately omits "minor children"
        self.assertNotIn("minor children", result.simplified_text)
        # Demo text is deliberately close to source but not identical
        self.assertIn(result.simplification_quality, ("simplified", "insufficient", "requires_human_review"))
        self.assertIsInstance(result.similarity_score, float)

    # Test 5: Missing document returns None
    async def test_missing_document_returns_none(self):
        """Non-existent document_id returns None."""
        service = SimplificationService(ai_provider=MockAIProvider())
        result = await service.simplify_chunk("nonexistent-doc", self.chunk_id)
        self.assertIsNone(result)

    # Test 6: Missing chunk returns None
    async def test_missing_chunk_returns_none(self):
        """Non-existent chunk_id returns None."""
        service = SimplificationService(ai_provider=MockAIProvider())
        result = await service.simplify_chunk(self.doc_id, "nonexistent-chunk-id")
        self.assertIsNone(result)

    # Test 7: Timeout during simplification raises TimeoutError
    async def test_timeout_raises(self):
        """Provider timeout propagates as TimeoutError."""
        provider = MockAIProvider(simulate_timeout=True)
        service = SimplificationService(ai_provider=provider)
        with self.assertRaises(TimeoutError):
            await service.simplify_chunk(self.doc_id, self.chunk_id)

    # Test 8: Reviewer failure falls back to requires_human_review
    async def test_reviewer_failure_fallback(self):
        """If Call 2 raises an exception, fidelity defaults to requires_human_review."""
        call_count = [0]

        class _BrokenReviewer(MockAIProvider):
            async def generate_grounded_answer(self, question, passages, system_instruction=None):
                call_count[0] += 1
                if call_count[0] == 1:
                    return GroundedAnswerResponse(
                        answer="Simplified text.",
                        insufficient_evidence=False,
                        cited_chunk_ids=[],
                        model_name="mock",
                        raw_response={},
                    )
                raise RuntimeError("Reviewer call failed")

        service = SimplificationService(ai_provider=_BrokenReviewer())
        result = await service.simplify_chunk(self.doc_id, self.chunk_id)
        self.assertEqual(result.fidelity.status, "requires_human_review")
        # simplification_quality and similarity_score must still be present
        self.assertIn(result.simplification_quality, ("simplified", "insufficient", "requires_human_review", "error"))
        self.assertIsInstance(result.similarity_score, float)

    # Test 9: Note field is always present
    async def test_note_always_present(self):
        """SemanticFidelityResult always carries a human verification note."""
        provider = _make_provider_for_simplify()
        service = SimplificationService(ai_provider=provider)
        result = await service.simplify_chunk(self.doc_id, self.chunk_id)
        self.assertTrue(len(result.fidelity.note) > 0)
        self.assertIn("human", result.fidelity.note.lower())

    # Test 10: Invalid reviewer status falls back to requires_human_review
    async def test_invalid_reviewer_status_fallback(self):
        """An unrecognised status string from the reviewer falls back gracefully."""
        provider = _make_provider_for_simplify(review_status="unknown_status_xyz")
        service = SimplificationService(ai_provider=provider)
        result = await service.simplify_chunk(self.doc_id, self.chunk_id)
        self.assertEqual(result.fidelity.status, "requires_human_review")
        self.assertIsInstance(result.similarity_score, float)

    # Test 11: Call 1 error does not produce spurious similarity score or execute Call 2
    async def test_call1_error_handling(self):
        """When Call 1 yields an error or unparseable output, quality is 'error' and Call 2 is bypassed."""
        err_doc_id = "doc-error-test"
        err_chunk_id = "chunk-err"
        save_document(err_doc_id, "test.pdf", [
            {"chunk_id": err_chunk_id, "page_number": 1, "text": "Unrelated unique administrative clause without demo matches."}
        ])
        provider = _make_provider_for_simplify(
            simplified_text="Unable to parse model output.",
            review_status="verified",
        )
        service = SimplificationService(ai_provider=provider)
        result = await service.simplify_chunk(err_doc_id, err_chunk_id)

        self.assertIsNotNone(result)
        self.assertEqual(result.simplification_quality, "error")
        self.assertEqual(result.fidelity.status, "requires_human_review")


# ---------------------------------------------------------------------------
# Deterministic transformation-check unit tests (no AI, no async)
# ---------------------------------------------------------------------------


class TestCheckTransformationQuality(unittest.TestCase):
    """
    Unit tests for check_transformation_quality().
    All tests are deterministic — no LLM calls.

    Thresholds under test:
      SIMILARITY_INSUFFICIENT = 0.85  for standard passages (>= 150 chars)
      SHORT_PASSAGE_REVIEW    = 0.70  for short passages   (<  150 chars)
    """

    # --- Standard-length passages (>= SHORT_PASSAGE_THRESHOLD) ---

    def test_identical_source_flagged_insufficient(self):
        """
        Unchanged source returns simplification_quality == 'insufficient'.
        Similarity at 1.0 (above 0.85 threshold).
        """
        source = _STANDARD_SOURCE  # 220+ chars
        quality, score = check_transformation_quality(source, source)
        self.assertEqual(quality, "insufficient")
        self.assertAlmostEqual(score, 1.0, places=2)

    def test_similarity_just_above_threshold_is_insufficient(self):
        """
        Similarity just above 0.85 → 'insufficient'.
        Achieved by making a minimal change to a long passage.
        """
        source = _STANDARD_SOURCE
        # Replace one word to push similarity just above 0.85
        # The source is ~220 chars; changing ~10 chars leaves similarity ~0.95
        modified = source.replace("Government employees", "Govt employees")
        quality, score = check_transformation_quality(source, modified)
        self.assertGreater(score, SIMILARITY_INSUFFICIENT)
        self.assertEqual(quality, "insufficient")

    def test_similarity_just_below_threshold_is_simplified(self):
        """
        Similarity just below 0.85 → 'simplified'.
        A genuinely rewritten passage must cross this threshold.
        """
        source = _STANDARD_SOURCE
        quality, score = check_transformation_quality(source, _STANDARD_SIMPLIFIED)
        self.assertLess(score, SIMILARITY_INSUFFICIENT)
        self.assertEqual(quality, "simplified")

    def test_very_different_text_is_simplified(self):
        """
        Completely different text → similarity near 0, quality == 'simplified'.
        """
        source = _STANDARD_SOURCE
        different = (
            "This is a completely different sentence unrelated to farming or benefits."
        )
        quality, score = check_transformation_quality(source, different)
        self.assertEqual(quality, "simplified")
        self.assertLess(score, 0.5)

    # --- Short passages (< SHORT_PASSAGE_THRESHOLD) ---

    def test_short_passage_high_similarity_requires_human_review(self):
        """
        Short passage (< 150 chars) with similarity > SHORT_PASSAGE_REVIEW (0.70)
        → 'requires_human_review' (not 'insufficient').
        Similarity scoring is unreliable for short inputs.
        """
        source = "Applicant must be below 18 years of age."  # ~40 chars
        # Near-identical version stays well above 0.70
        near_identical = "Applicant must be under 18 years of age."
        quality, score = check_transformation_quality(source, near_identical)
        self.assertLess(len(source), SHORT_PASSAGE_THRESHOLD)
        self.assertGreater(score, SHORT_PASSAGE_REVIEW)
        self.assertEqual(quality, "requires_human_review")

    def test_short_passage_low_similarity_is_simplified(self):
        """
        Short passage (< 150 chars) with similarity <= SHORT_PASSAGE_REVIEW (0.70)
        → 'simplified' (reliable enough to classify).
        """
        source = "Applicant must be below 18 years of age."  # ~40 chars
        rewritten = "Only people younger than eighteen years old can apply."
        quality, score = check_transformation_quality(source, rewritten)
        self.assertLess(len(source), SHORT_PASSAGE_THRESHOLD)
        self.assertLessEqual(score, SHORT_PASSAGE_REVIEW)
        self.assertEqual(quality, "simplified")

    # --- Score range invariant ---

    def test_similarity_score_always_between_zero_and_one(self):
        """similarity_score must always be in [0, 1]."""
        cases = [
            (_STANDARD_SOURCE, _STANDARD_SOURCE),
            (_STANDARD_SOURCE, _STANDARD_SIMPLIFIED),
            (_STANDARD_SOURCE, ""),
            ("", ""),
        ]
        for source, simplified in cases:
            _, score = check_transformation_quality(source, simplified)
            src_repr = repr(source[:30])
            self.assertGreaterEqual(score, 0.0, msg=f"score={score} for source={src_repr}")
            self.assertLessEqual(score, 1.0, msg=f"score={score} for source={src_repr}")


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestSemanticFidelitySchema(unittest.TestCase):
    """Unit tests for the SemanticFidelityResult and SimplificationResponse schemas."""

    def test_default_note_present(self):
        result = SemanticFidelityResult(status="verified")
        self.assertIn("human", result.note.lower())

    def test_controlled_demo_flag_default_false(self):
        result = SemanticFidelityResult(status="potential_issue")
        self.assertFalse(result.controlled_demo)

    def test_simplification_response_requires_quality_and_score(self):
        """SimplificationResponse must carry both new fields."""
        fidelity = SemanticFidelityResult(status="verified")
        response = SimplificationResponse(
            chunk_id="test-chunk",
            source_passage="Source.",
            simplified_text="Simpler.",
            simplification_quality="simplified",
            similarity_score=0.42,
            fidelity=fidelity,
        )
        self.assertEqual(response.simplification_quality, "simplified")
        self.assertAlmostEqual(response.similarity_score, 0.42)
        self.assertEqual(response.fidelity.status, "verified")
        self.assertFalse(response.controlled_demo)

    def test_simplification_response_all_quality_values_accepted(self):
        """All four Literal values are accepted by the schema."""
        fidelity = SemanticFidelityResult(status="verified")
        for quality in ("simplified", "insufficient", "requires_human_review", "error"):
            response = SimplificationResponse(
                chunk_id="c",
                source_passage="s",
                simplified_text="t",
                simplification_quality=quality,
                similarity_score=0.5,
                fidelity=fidelity,
            )
            self.assertEqual(response.simplification_quality, quality)


if __name__ == "__main__":
    unittest.main()
