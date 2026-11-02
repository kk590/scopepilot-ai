"""
LLM-backed agents ONLY.
Exactly two agents:
  1. ScopeIntelligenceAgent  – Llama via OpenRouter
  2. VerifierLoopAgent       – Mistral via OpenRouter
No other LLM calls exist in the system.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.config import get_settings
from app.database.schemas import ProjectScope, StructuredRequirements, VerificationResult

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseLLMAgent:
    def __init__(self, model: str):
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        self.model = model

    async def _chat(self, system: str, user: str, temperature: float = 0.2) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or "{}"

    def _extract_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(
                lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            )
        return json.loads(text)


class ScopeIntelligenceAgent(BaseLLMAgent):
    """Produces and corrects project scopes from structured requirements."""

    def __init__(self):
        super().__init__(settings.openrouter_scope_model)

    async def generate(self, requirements: StructuredRequirements) -> ProjectScope:
        system = (
            "You are a senior project scoping expert. "
            "Convert structured requirements into a clear, complete project scope. "
            "Return valid JSON with fields: summary (str), features (list of "
            "{name, description, priority}), assumptions (list[str]), "
            "constraints (list[str]), out_of_scope (list[str]), timeline_weeks (int|null)."
        )
        user = f"Requirements:\n{requirements.model_dump_json(indent=2)}"
        raw = await self._chat(system, user)
        try:
            data = self._extract_json(raw)
            return ProjectScope.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Scope agent returned invalid JSON: %s", raw[:500])
            raise ValueError(f"ScopeIntelligenceAgent produced invalid output: {exc}") from exc

    async def correct(self, scope: ProjectScope, feedback: str) -> ProjectScope:
        system = (
            "You are a senior project scoping expert. "
            "Revise the given scope based on the verifier feedback. "
            "Return the full corrected scope as valid JSON with the same schema."
        )
        user = (
            f"Current scope:\n{scope.model_dump_json(indent=2)}\n\n"
            f"Verifier feedback:\n{feedback}"
        )
        raw = await self._chat(system, user)
        try:
            data = self._extract_json(raw)
            return ProjectScope.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Scope correct returned invalid JSON: %s", raw[:500])
            raise ValueError(f"ScopeIntelligenceAgent.correct produced invalid output: {exc}") from e


class VerifierLoopAgent(BaseLLMAgent):
    """Verifies a scope for completeness, consistency and feasibility."""

    def __init__(self):
        super().__init__(settings.openrouter_verifier_model)

    async def verify(self, scope: ProjectScope) -> VerificationResult:
        system = (
            "You are a strict project scope verifier. "
            "Check the scope for completeness, internal consistency, "
            "realistic timeline, clear acceptance criteria, and missing risks. "
            "Return JSON: {\"verified\": bool, \"feedback\": str, \"issues\": list[str]}."
        )
        user = f"Scope to verify:\n{scope.model_dump_json(indent=2)}"
        raw = await self._chat(system, user, temperature=0.1)
        try:
            data = self._extract_json(raw)
            if "issues" not in data:
                data["issues"] = []
            return VerificationResult.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Verifier agent returned invalid JSON: %s", raw[:500])
            raise ValueError(f"VerifierLoopAgent produced invalid output: {exc}") from exc
