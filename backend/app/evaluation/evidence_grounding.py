"""
Evidence Grounding evaluation module for CDTM dimension c.

Evaluates whether generated answers are strictly grounded in retrieved evidence.
Combines deterministic citation-ID validation with a claim-level AI review pass.

CRITICAL INVARIANTS:
1. Every cited chunk ID must belong to the requested document in the store.
2. Valid citation IDs alone do NOT prove that claims are supported.
3. The AI reviewer assesses whether individual factual claims are supported by the passages.
"""
import logging
from typing import Any, Literal
from pydantic import BaseModel, Field

from app.ai.base import AIProvider
from app.document.store import get_document

logger = logging.getLogger(__name__)


class ClaimSupportItem(BaseModel):
    """Evaluation of an individual factual claim against cited passages."""

    claim: str = Field(description="The atomic factual claim made in the answer.")
    supported: bool = Field(description="True if the claim is directly corroborated by cited passages.")
    citing_chunk_ids: list[str] = Field(default_factory=list, description="Chunk IDs supporting this claim.")
    reasoning: str = Field(default="", description="Brief justification for support determination.")


class EvidenceGroundingResult(BaseModel):
    """
    Result of claim-level Evidence Grounding evaluation (CDTM Dimension c).

    Statuses:
      grounded              — All identified factual claims are directly corroborated by valid cited passages.
      partially_grounded    — Some claims are supported, but one or more claims lack evidence in cited passages.
      ungrounded            — Factual claims were made without valid citations or without passage support.
      abstained             — System explicitly abstained due to insufficient or unretrieved evidence.
      requires_human_review — Evaluation was uncertain, reviewer timed out, or passage claims are ambiguous.
      not_evaluated         — Required inputs (e.g. document or inquiry) are unavailable.
    """

    status: Literal[
        "grounded",
        "partially_grounded",
        "ungrounded",
        "abstained",
        "requires_human_review",
        "not_evaluated",
    ] = Field(description="Evidence grounding status.")
    cited_chunk_ids: list[str] = Field(default_factory=list)
    valid_chunk_ids: list[str] = Field(default_factory=list)
    invalid_chunk_ids: list[str] = Field(default_factory=list)
    claims: list[ClaimSupportItem] = Field(default_factory=list)
    supported_claims_count: int = Field(default=0)
    unsupported_claims_count: int = Field(default=0)
    note: str = Field(
        default=(
            "AI-assisted evidence grounding evaluation. Assesses claim-level support against cited passages. "
            "Valid citation IDs alone do not constitute factual verification without human inspection."
        )
    )
    controlled_demo: bool = Field(default=False)


GROUNDING_REVIEW_SYSTEM_PROMPT = """You are an independent AI evidence grounding auditor for administrative document Q&A.

Your task is to break down a generated ANSWER into individual factual claims and check whether EACH claim is directly supported by the provided CITED PASSAGES.

RULES:
1. Extract atomic factual claims made in the ANSWER.
2. For each claim, check whether the text in CITED PASSAGES directly corroborates it.
3. If an answer makes a statement not supported by the cited passages (or goes beyond them), mark supported as false.
4. If the answer explicitly states that evidence is insufficient or abstains, identify that.

You must respond with ONLY a valid JSON object in this exact format:
{
  "claims": [
    {
      "claim": "<statement made in the answer>",
      "supported": true,
      "citing_chunk_ids": ["<matching chunk id>"],
      "reasoning": "<brief explanation>"
    }
  ]
}
"""


class EvidenceGroundingEvaluator:
    """Evaluates Evidence Grounding by verifying citations and auditing claim support."""

    def __init__(self, ai_provider: AIProvider | None = None) -> None:
        self._provider = ai_provider

    async def evaluate_grounding(
        self,
        document_id: str,
        answer: str,
        cited_chunk_ids: list[str],
        insufficient_evidence: bool = False,
        demo: bool = False,
    ) -> EvidenceGroundingResult:
        """
        Evaluate claim-level grounding of an answer against actual cited passages
        resolved from the document store.
        """
        clean_answer = answer.strip()
        if not clean_answer:
            return EvidenceGroundingResult(
                status="not_evaluated",
                note="Answer text is empty. Evidence grounding cannot be evaluated.",
                controlled_demo=demo,
            )

        # 1. Check abstention
        if insufficient_evidence or (not cited_chunk_ids and "insufficient" in clean_answer.lower()):
            return EvidenceGroundingResult(
                status="abstained",
                cited_chunk_ids=[],
                valid_chunk_ids=[],
                invalid_chunk_ids=[],
                claims=[],
                note="System explicitly abstained due to insufficient verifiable evidence.",
                controlled_demo=demo,
            )

        # 2. Resolve document and validate cited chunk IDs
        doc = get_document(document_id)
        if doc is None:
            return EvidenceGroundingResult(
                status="not_evaluated",
                note=f"Document '{document_id}' not found in store.",
                controlled_demo=demo,
            )

        # Map document chunks
        stored_chunks = {c["chunk_id"]: c for c in doc.get("chunks", []) if "chunk_id" in c}

        valid_ids: list[str] = []
        invalid_ids: list[str] = []
        cited_passages: list[dict[str, Any]] = []

        for cid in cited_chunk_ids:
            if cid in stored_chunks:
                if cid not in valid_ids:
                    valid_ids.append(cid)
                    cited_passages.append(stored_chunks[cid])
            else:
                if cid not in invalid_ids:
                    invalid_ids.append(cid)

        # 3. Deterministic check: citations missing or fabricated
        if not cited_chunk_ids:
            return EvidenceGroundingResult(
                status="ungrounded",
                cited_chunk_ids=[],
                valid_chunk_ids=[],
                invalid_chunk_ids=[],
                note="The generated answer made substantive claims but provided zero citations.",
                unsupported_claims_count=1,
                controlled_demo=demo,
            )

        if not valid_ids:
            return EvidenceGroundingResult(
                status="ungrounded",
                cited_chunk_ids=cited_chunk_ids,
                valid_chunk_ids=[],
                invalid_chunk_ids=invalid_ids,
                note="All cited chunk IDs are invalid or fabricated; none belong to the requested document.",
                unsupported_claims_count=len(cited_chunk_ids),
                controlled_demo=demo,
            )

        # 4. If no AI provider is configured, return deterministic status
        if self._provider is None:
            return EvidenceGroundingResult(
                status="requires_human_review",
                cited_chunk_ids=cited_chunk_ids,
                valid_chunk_ids=valid_ids,
                invalid_chunk_ids=invalid_ids,
                note="Deterministic citations verified; AI claim support reviewer not configured.",
                controlled_demo=demo,
            )

        # 5. AI Claim-Support Review Pass
        prompt_text = (
            f"ANSWER TO EVALUATE:\n{clean_answer}\n\n"
            "CITED PASSAGES:\n"
        )
        for p in cited_passages:
            prompt_text += f"[{p.get('chunk_id')}]: {p.get('text', '')}\n\n"

        try:
            generation = await self._provider.generate_grounded_answer(
                question="Evaluate whether all claims in the answer are supported by the cited passages.",
                passages=cited_passages,
                system_instruction=GROUNDING_REVIEW_SYSTEM_PROMPT,
            )
            raw = generation.raw_response or {}
            raw_claims = raw.get("claims", [])

            claim_items: list[ClaimSupportItem] = []
            supported_count = 0
            unsupported_count = 0

            for rc in raw_claims:
                if isinstance(rc, dict):
                    c_text = str(rc.get("claim", "")).strip()
                    c_sup = bool(rc.get("supported", False))
                    c_ids = [str(x) for x in rc.get("citing_chunk_ids", []) if x]
                    c_reason = str(rc.get("reasoning", "")).strip()

                    if c_text:
                        claim_items.append(
                            ClaimSupportItem(
                                claim=c_text,
                                supported=c_sup,
                                citing_chunk_ids=c_ids,
                                reasoning=c_reason,
                            )
                        )
                        if c_sup:
                            supported_count += 1
                        else:
                            unsupported_count += 1

            if not claim_items:
                # If reviewer failed to parse claims cleanly
                status: Literal["grounded", "partially_grounded", "ungrounded", "abstained", "requires_human_review", "not_evaluated"] = (
                    "requires_human_review"
                )
            elif unsupported_count == 0 and not invalid_ids:
                status = "grounded"
            elif supported_count > 0 and (unsupported_count > 0 or invalid_ids):
                status = "partially_grounded"
            else:
                status = "ungrounded"

            return EvidenceGroundingResult(
                status=status,
                cited_chunk_ids=cited_chunk_ids,
                valid_chunk_ids=valid_ids,
                invalid_chunk_ids=invalid_ids,
                claims=claim_items,
                supported_claims_count=supported_count,
                unsupported_claims_count=unsupported_count + len(invalid_ids),
                note="Claim-level evidence grounding audit completed against actual store passages.",
                controlled_demo=demo,
            )

        except Exception as exc:
            logger.warning("Evidence grounding evaluation failed: %s", str(exc))
            return EvidenceGroundingResult(
                status="requires_human_review",
                cited_chunk_ids=cited_chunk_ids,
                valid_chunk_ids=valid_ids,
                invalid_chunk_ids=invalid_ids,
                note=f"Reviewer encountered an error: {str(exc)}. Manual inspection required.",
                controlled_demo=demo,
            )
