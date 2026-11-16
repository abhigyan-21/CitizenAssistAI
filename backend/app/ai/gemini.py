import asyncio
import json
import logging
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field

from app.ai.base import AIProvider, GroundedAnswerResponse

logger = logging.getLogger(__name__)


class _GroundedAnswerSchema(BaseModel):
    answer: str = Field(
        description="Simple English answer strictly grounded in the provided passages, or a clear explanation of what is missing."
    )
    insufficient_evidence: bool = Field(
        description="True if the provided passages do not contain enough facts to answer the question, false otherwise."
    )
    cited_chunk_ids: list[str] = Field(
        default_factory=list,
        description="List of exact chunk_id strings from the provided passages supporting the answer."
    )


DEFAULT_SYSTEM_INSTRUCTION = (
    "You are an evidence-grounded administrative document inquiry assistant.\n"
    "Your duty is to answer the citizen's inquiry using EXCLUSIVELY the provided source passages.\n\n"
    "STRICT GROUNDING & CITATION RULES:\n"
    "1. Base your answer ONLY on facts explicitly stated in the provided passages.\n"
    "2. Do NOT use outside knowledge, prior training assumptions, or extrapolate.\n"
    "3. If the provided passages do not contain sufficient evidence to answer the question, "
    "set insufficient_evidence to true, and explain clearly in simple English that the provided "
    "document passages do not contain the answer.\n"
    "4. For every factual claim, include the exact chunk_id(s) in cited_chunk_ids.\n"
    "5. Only cite chunk_ids that are present in the supplied passages. Never invent chunk IDs.\n"
    "6. Do not invent dates, financial amounts, family definitions, or eligibility conditions.\n"
    "7. Answer in clear, concise, neutral English."
)


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider utilizing the official google-genai SDK."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-3.8-flash",
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided to initialize GeminiProvider.")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        # Instantiate asynchronous client via official SDK
        self.client = genai.Client(api_key=self.api_key)

    async def generate_grounded_answer(
        self,
        question: str,
        passages: list[dict],
        system_instruction: str | None = None,
    ) -> GroundedAnswerResponse:
        """Execute asynchronous generation with structured output enforcement."""
        sys_inst = system_instruction or DEFAULT_SYSTEM_INSTRUCTION

        # Format retrieved passages clearly with chunk_id and page_number
        passages_text_blocks = []
        for idx, p in enumerate(passages, start=1):
            chunk_id = p.get("chunk_id", f"chunk-{idx}")
            page_num = p.get("page_number", "Unknown")
            text = p.get("text", "").strip()
            passages_text_blocks.append(
                f"[PASSAGE {idx}] (chunk_id: {chunk_id}, page: {page_num})\n{text}"
            )

        passages_formatted = "\n\n".join(passages_text_blocks)
        user_prompt = (
            f"PROVIDED SOURCE PASSAGES:\n{passages_formatted}\n\n"
            f"CITIZEN QUESTION:\n{question}\n\n"
            "Respond strictly in structured JSON matching the defined schema."
        )

        config = types.GenerateContentConfig(
            system_instruction=sys_inst,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=_GroundedAnswerSchema,
        )

        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=config,
                ),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.error("Gemini API call timed out after %s seconds", self.timeout_seconds)
            raise TimeoutError(f"Gemini request timed out after {self.timeout_seconds}s") from exc
        except genai_errors.APIError as exc:
            logger.error("Gemini API returned error: %s (code: %s)", exc.message, getattr(exc, "code", None))
            raise exc
        except Exception as exc:
            logger.error("Unexpected error invoking Gemini API: %s", str(exc))
            raise exc

        # Parse structured output safely
        raw_text = response.text or ""
        try:
            parsed = json.loads(raw_text)
            return GroundedAnswerResponse(
                answer=parsed.get("answer", "").strip(),
                insufficient_evidence=bool(parsed.get("insufficient_evidence", False)),
                cited_chunk_ids=list(parsed.get("cited_chunk_ids", [])),
                model_name=self.model_name,
                raw_response=parsed,
            )
        except Exception as exc:
            logger.warning("Failed to parse structured JSON from model response: %s", raw_text)
            return GroundedAnswerResponse(
                answer=raw_text if raw_text else "Unable to parse model output.",
                insufficient_evidence=True,
                cited_chunk_ids=[],
                model_name=self.model_name,
                raw_response={"raw_text": raw_text, "parse_error": str(exc)},
            )
