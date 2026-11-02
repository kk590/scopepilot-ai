"""Deterministic parser shell agent – extracts structured requirements from free text."""

from __future__ import annotations

import logging
import re
from typing import List

from app.database.schemas import FeatureItem, StructuredRequirements

logger = logging.getLogger(__name__)


class ParserAgent:
    """Rule-based + lightweight heuristic parser. No LLM calls."""

    async def parse(self, text: str) -> StructuredRequirements:
        text = text.strip()
        if not text:
            return StructuredRequirements(
                missing_info=["Please provide a description of the project requirements."]
            )

        features = self._extract_features(text)
        constraints = self._extract_constraints(text)
        timeline = self._extract_timeline(text)
        missing = self._detect_missing(text, features, timeline)

        summary = text[:300] + ("..." if len(text) > 300 else "")

        return StructuredRequirements(
            summary=summary,
            features=features,
            constraints=constraints,
            assumptions=[],
            timeline_weeks=timeline,
            missing_info=missing,
        )

    def _extract_features(self, text: str) -> List[FeatureItem]:
        features = []
        # Simple heuristic: sentences or bullet-like phrases
        candidates = re.split(r"[.;\n]+", text)
        for c in candidates:
            c = c.strip()
            if len(c) < 15:
                continue
            # Look for action-oriented phrases
            if any(
                kw in c.lower()
                for kw in [
                    "need",
                    "want",
                    "should",
                    "must",
                    "login",
                    "view",
                    "download",
                    "portal",
                    "dashboard",
                    "report",
                    "mobile",
                    "api",
                    "integrate",
                ]
            ):
                name = c[:60].rsplit(" ", 1)[0] if len(c) > 60 else c
                features.append(
                    FeatureItem(name=name.strip(), description=c, priority="medium")
                )
        if not features:
            features.append(
                FeatureItem(
                    name="Core functionality",
                    description=text[:200],
                    priority="high",
                )
            )
        return features[:12]  # cap

    def _extract_constraints(self, text: str) -> List[str]:
        constraints = []
        lower = text.lower()
        if "mobile" in lower or "responsive" in lower:
            constraints.append("Must be mobile-responsive")
        if "week" in lower or "month" in lower:
            constraints.append("Timeline constraints present in requirements")
        if "budget" in lower or "cost" in lower:
            constraints.append("Budget considerations mentioned")
        return constraints

    def _extract_timeline(self, text: str) -> int | None:
        # Look for "X weeks" or "X months"
        m = re.search(r"(\d+)\s*weeks?", text, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"(\d+)\s*months?", text, re.I)
        if m:
            return int(m.group(1)) * 4
        return None

    def _detect_missing(
        self, text: str, features: List[FeatureItem], timeline: int | None
    ) -> List[str]:
        missing = []
        if len(features) < 2:
            missing.append("Please list the main features or user stories in more detail.")
        if timeline is None:
            missing.append("What is the desired timeline or deadline?")
        if "login" not in text.lower() and "auth" not in text.lower():
            # only if it looks like a user-facing app
            if any(k in text.lower() for k in ["portal", "dashboard", "app", "website"]):
                missing.append("Do users need to log in? Any authentication requirements?")
        return missing
