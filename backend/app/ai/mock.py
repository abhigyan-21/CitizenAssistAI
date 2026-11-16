from typing import Any
from app.ai.base import AIProvider, GroundedAnswerResponse


class MockAIProvider(AIProvider):
    """
    Configurable Mock AI Provider for automated testing without network access.
    """

    def __init__(
        self,
        mock_answer: str = "This is a grounded answer from the mock provider.",
        mock_insufficient_evidence: bool = False,
        mock_cited_chunk_ids: list[str] | None = None,
        mock_model_name: str = "mock-model",
        simulate_timeout: bool = False,
        simulate_error: Exception | None = None,
    ) -> None:
        self.mock_answer = mock_answer
        self.mock_insufficient_evidence = mock_insufficient_evidence
        self.mock_cited_chunk_ids = mock_cited_chunk_ids or []
        self.mock_model_name = mock_model_name
        self.simulate_timeout = simulate_timeout
        self.simulate_error = simulate_error
        self.call_count = 0
        self.last_question: str | None = None
        self.last_passages: list[dict] | None = None

    async def generate_grounded_answer(
        self,
        question: str,
        passages: list[dict],
        system_instruction: str | None = None,
    ) -> GroundedAnswerResponse:
        self.call_count += 1
        self.last_question = question
        self.last_passages = passages

        if self.simulate_timeout:
            raise TimeoutError("Simulated Gemini provider timeout")

        if self.simulate_error:
            raise self.simulate_error

        # If mock_cited_chunk_ids is not explicitly set, default to citing the first passage if available
        cited_ids = self.mock_cited_chunk_ids
        if not cited_ids and passages and not self.mock_insufficient_evidence:
            cited_ids = [passages[0].get("chunk_id", "")]

        return GroundedAnswerResponse(
            answer=self.mock_answer,
            insufficient_evidence=self.mock_insufficient_evidence,
            cited_chunk_ids=cited_ids,
            model_name=self.mock_model_name,
            raw_response={"mock": True},
        )
