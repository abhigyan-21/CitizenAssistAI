"""
Groq AI Provider for CitizenAssist AI.

Uses the official `groq` Python SDK with its asynchronous client.
Structured output is achieved via JSON Object Mode + strict Pydantic validation.
"""
import asyncio
import json
import logging
import re
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

    async def _create_completion_with_rate_limit_retry(
        self,
        messages: list[dict],
        response_format: dict[str, str] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Any:
        """
        Executes a Groq chat completion call with at most one transient 429 retry
        and graceful JSON validation error fallback.
        """
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        try:
            return await asyncio.wait_for(
                self.client.chat.completions.create(**kwargs),
                timeout=self.timeout_seconds,
            )
        except groq_sdk.BadRequestError as b_exc:
            # If JSON validation failed on Groq's proxy, retry without JSON mode
            if response_format and "json" in str(b_exc).lower():
                logger.warning(
                    "Groq JSON mode validation rejected; retrying without response_format constraint: %s",
                    b_exc,
                )
                kwargs_no_json = dict(kwargs)
                kwargs_no_json.pop("response_format", None)
                return await asyncio.wait_for(
                    self.client.chat.completions.create(**kwargs_no_json),
                    timeout=self.timeout_seconds,
                )
            raise b_exc
        except groq_sdk.RateLimitError as r_exc:
            # Single transient 429 retry using provider guidance
            retry_wait = 3.0
            match = re.search(r"try again in ([\d\.]+)s", str(r_exc))
            if match:
                try:
                    retry_wait = min(10.0, float(match.group(1)))
                except ValueError:
                    pass
            logger.warning(
                "Groq rate limit reached (429). Waiting %.1fs for single transient retry...",
                retry_wait,
            )
            await asyncio.sleep(retry_wait)
            try:
                return await asyncio.wait_for(
                    self.client.chat.completions.create(**kwargs),
                    timeout=self.timeout_seconds,
                )
            except (groq_sdk.RateLimitError, groq_sdk.BadRequestError) as sec_exc:
                secondary_model = "llama-3.1-8b-instant" if self.model_name != "llama-3.1-8b-instant" else "llama-3.3-70b-versatile"
                logger.warning("Primary model failed after retry. Attempting secondary model '%s'...", secondary_model)
                kwargs_sec = dict(kwargs, model=secondary_model)
                try:
                    return await asyncio.wait_for(
                        self.client.chat.completions.create(**kwargs_sec),
                        timeout=self.timeout_seconds,
                    )
                except Exception:
                    raise sec_exc

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
            response = await self._create_completion_with_rate_limit_retry(
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=4096,
                temperature=0.0,
            )
        except asyncio.TimeoutError as exc:
            logger.error("Groq API call timed out after %s seconds", self.timeout_seconds)
            raise TimeoutError(f"Groq request timed out after {self.timeout_seconds}s") from exc
        except groq_sdk.AuthenticationError as exc:
            logger.error("Groq authentication failed: %s", exc.message)
            raise RuntimeError("Groq authentication failed. Check GROQ_API_KEY.") from exc
        except groq_sdk.RateLimitError as exc:
            logger.error("Groq rate limit exceeded: %s", exc.message)
            raise exc
        except groq_sdk.APITimeoutError as exc:
            logger.error("Groq SDK-level timeout: %s", str(exc))
            raise TimeoutError("Groq SDK request timed out.") from exc
        except groq_sdk.APIConnectionError as exc:
            logger.error("Groq API connection error: %s", str(exc))
            raise RuntimeError(f"Groq connection error: {exc}") from exc
        except groq_sdk.APIStatusError as exc:
            logger.error("Groq API status error: %s (status: %s)", exc.message, exc.status_code)
            raise exc
        except Exception as exc:
            logger.error("Unexpected error invoking Groq API: %s", str(exc))
            raise exc

        # Inspect completion choice
        if not response.choices:
            raise RuntimeError("Groq API returned an empty choices list.")

        choice = response.choices[0]
        raw_text = (choice.message.content or "").strip()
        finish_reason = getattr(choice, "finish_reason", "unknown")

        if not raw_text:
            if finish_reason == "length":
                raise RuntimeError(
                    "Groq completion reached max_tokens token budget before producing output."
                )
            raise RuntimeError(
                f"Groq model returned an empty response (finish_reason: '{finish_reason}')."
            )

        # Priority JSON Parser:
        # 1. Standard JSON
        # 2. Fenced code blocks (```json ... ```)
        # 3. Balanced outer JSON object ({...})
        parsed: dict[str, Any] | None = None

        # Priority 1: Direct JSON parse
        try:
            candidate = json.loads(raw_text)
            if isinstance(candidate, dict):
                parsed = candidate
        except Exception:
            pass

        # Priority 2: Fenced code block ```json ... ```
        if parsed is None and "```" in raw_text:
            fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
            if fenced:
                try:
                    candidate = json.loads(fenced.group(1).strip())
                    if isinstance(candidate, dict):
                        parsed = candidate
                except Exception:
                    pass

        # Priority 3: Extract outer balanced JSON object
        if parsed is None:
            start_i = raw_text.find("{")
            end_i = raw_text.rfind("}")
            if start_i != -1 and end_i > start_i:
                try:
                    candidate = json.loads(raw_text[start_i : end_i + 1])
                    if isinstance(candidate, dict):
                        parsed = candidate
                except Exception:
                    pass

        if parsed is not None:
            # Priority 4: Check alternative keys
            resolved_answer = ""
            for key in ("answer", "simplified_text", "text", "content", "translation"):
                val = parsed.get(key)
                if isinstance(val, str) and val.strip():
                    resolved_answer = val.strip()
                    break

            # Priority 5: Validate resulting structure
            return GroundedAnswerResponse(
                answer=resolved_answer or (
                    str(parsed.get("status", "")) if "status" in parsed else str(parsed)
                ),
                insufficient_evidence=bool(parsed.get("insufficient_evidence", False)),
                cited_chunk_ids=list(parsed.get("cited_chunk_ids", [])),
                model_name=self.model_name,
                raw_response=parsed,
            )

        # Fallback when model output cannot be parsed into structured JSON
        logger.warning("Failed to parse structured JSON from Groq response: %s", raw_text[:200])
        return GroundedAnswerResponse(
            answer="Unable to parse model output.",
            insufficient_evidence=True,
            cited_chunk_ids=[],
            model_name=self.model_name,
            raw_response={"raw_text": raw_text, "parse_error": "Failed to parse structured JSON"},
        )

    async def generate_basic_answer(
        self,
        question: str,
        passages: list[dict],
    ) -> str:
        """
        Generate an unconstrained baseline generative answer without CDTM citation enforcement or claim auditing.
        """
        passage_texts = "\n\n".join(
            p.get("text", "").strip() for p in passages if p.get("text")
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant answering citizen questions based on an administrative document. "
                    "Provide a direct, helpful, and natural response to the question using the provided context."
                ),
            },
            {
                "role": "user",
                "content": f"Document context:\n{passage_texts}\n\nQuestion: {question}",
            },
        ]
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=2048,
                ),
                timeout=self.timeout_seconds,
            )
            choice = response.choices[0] if response.choices else None
            return choice.message.content.strip() if choice and choice.message.content else "No response generated."
        except asyncio.TimeoutError as exc:
            raise TimeoutError(f"Groq request timed out after {self.timeout_seconds}s") from exc
        except groq_sdk.AuthenticationError as exc:
            raise RuntimeError("Groq authentication failed. Check GROQ_API_KEY.") from exc
        except groq_sdk.RateLimitError as exc:
            raise exc
        except groq_sdk.APITimeoutError as exc:
            raise TimeoutError("Groq SDK request timed out.") from exc
        except Exception as exc:
            logger.error("Groq basic generation error: %s", exc)
            raise
