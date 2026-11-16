"""
Groq AI Provider for CitizenAssist AI.

Uses the official `groq` Python SDK with its asynchronous client.
Structured output is achieved via JSON Object Mode + strict Pydantic validation.
"""
import asyncio
import json
import logging
from typing import Any

import groq as groq_sdk
from groq import AsyncGroq
from pydantic import ValidationError

from app.ai.base import AIProvider, GroundedAnswerResponse

logger = logging.getLogger(__name__)

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
    "7. Answer in clear, concise, neutral English.\n\n"
    "RESPONSE FORMAT — You MUST respond with ONLY valid JSON, no prose before or after:\n"
    "{\n"
    '  "answer": "<your grounded answer or abstention explanation>",\n'
    '  "insufficient_evidence": <true|false>,\n'
    '  "cited_chunk_ids": ["<chunk_id_1>", "<chunk_id_2>"]\n'
    "}"
)


class GroqProvider(AIProvider):
    """
    Groq AI Provider using the official `groq` SDK AsyncGroq client.

    Uses JSON Object Mode for structured output, followed by strict
    Pydantic validation against GroundedAnswerResponse.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "llama-3.3-70b-versatile",
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("GROQ_API_KEY must be provided to initialise GroqProvider.")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        # max_retries=0: surface errors immediately without hidden retry latency
        self.client = AsyncGroq(
            api_key=api_key.strip(),
            max_retries=0,
        )

    async def generate_grounded_answer(
        self,
        question: str,
        passages: list[dict],
        system_instruction: str | None = None,
    ) -> GroundedAnswerResponse:
        """
        Execute asynchronous Groq chat completion with JSON Object Mode.
        Validates the returned JSON strictly against GroundedAnswerResponse.
        """
        sys_inst = system_instruction or DEFAULT_SYSTEM_INSTRUCTION

        # Format retrieved passages with chunk_id and page_number
        passage_blocks: list[str] = []
        for idx, p in enumerate(passages, start=1):
            chunk_id = p.get("chunk_id", f"chunk-{idx}")
            page_num = p.get("page_number", "Unknown")
            text = p.get("text", "").strip()
            passage_blocks.append(
                f"[PASSAGE {idx}] (chunk_id: {chunk_id}, page: {page_num})\n{text}"
            )

        passages_formatted = "\n\n".join(passage_blocks)
        user_prompt = (
            f"PROVIDED SOURCE PASSAGES:\n{passages_formatted}\n\n"
            f"CITIZEN QUESTION:\n{question}\n\n"
            "Respond with ONLY the JSON object as instructed. No additional text."
        )

        messages = [
            {"role": "system", "content": sys_inst},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                ),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.error(
                "Groq API call timed out after %s seconds", self.timeout_seconds
            )
            raise TimeoutError(
                f"Groq request timed out after {self.timeout_seconds}s"
            ) from exc
        except groq_sdk.AuthenticationError as exc:
            logger.error("Groq authentication failed: %s", exc.message)
            raise RuntimeError(
                "Groq authentication failed. Check GROQ_API_KEY."
            ) from exc
        except groq_sdk.RateLimitError as exc:
            logger.error("Groq rate limit exceeded: %s", exc.message)
            # Re-raise as a known type; routes.py maps this to HTTP 429
            raise exc
        except groq_sdk.APITimeoutError as exc:
            logger.error("Groq SDK-level timeout: %s", str(exc))
            raise TimeoutError("Groq SDK request timed out.") from exc
        except groq_sdk.APIConnectionError as exc:
            logger.error("Groq API connection error: %s", str(exc))
            raise RuntimeError(f"Groq connection error: {exc}") from exc
        except groq_sdk.APIStatusError as exc:
            logger.error(
                "Groq API status error: %s (status: %s)", exc.message, exc.status_code
            )
            raise exc
        except Exception as exc:
            logger.error("Unexpected error invoking Groq API: %s", str(exc))
            raise exc

        # Extract text from first choice
        raw_text: str = ""
        if response.choices:
            raw_text = (response.choices[0].message.content or "").strip()

        # Strict Pydantic validation of structured JSON response
        try:
            parsed: dict[str, Any] = json.loads(raw_text)
            return GroundedAnswerResponse(
                answer=str(parsed.get("answer", "")).strip(),
                insufficient_evidence=bool(parsed.get("insufficient_evidence", False)),
                cited_chunk_ids=list(parsed.get("cited_chunk_ids", [])),
                model_name=self.model_name,
                raw_response=parsed,
            )
        except (json.JSONDecodeError, ValidationError, Exception) as exc:
            logger.warning(
                "Failed to parse structured JSON from Groq response: %s", raw_text
            )
            return GroundedAnswerResponse(
                answer=raw_text if raw_text else "Unable to parse model output.",
                insufficient_evidence=True,
                cited_chunk_ids=[],
                model_name=self.model_name,
                raw_response={"raw_text": raw_text, "parse_error": str(exc)},
            )
