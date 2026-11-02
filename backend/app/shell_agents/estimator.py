"""Deterministic estimation shell agent."""

from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.database.schemas import ProjectEstimate, ProjectScope

logger = logging.getLogger(__name__)
settings = get_settings()


class EstimationAgent:
    """Simple heuristic estimator – no LLM."""

    async def estimate(self, scope: ProjectScope | dict[str, Any]) -> ProjectEstimate:
        if hasattr(scope, "model_dump"):
            data = scope.model_dump()
        else:
            data = scope

        features = data.get("features") or []
        timeline_weeks = data.get("timeline_weeks") or 8

        # Base hours per feature by priority
        hours = 0.0
        breakdown: dict[str, float] = {}
        for f in features:
            if isinstance(f, dict):
                name = f.get("name", "feature")
                prio = (f.get("priority") or "medium").lower()
            else:
                name = getattr(f, "name", "feature")
                prio = getattr(f, "priority", "medium").lower()

            h = {"high": 40.0, "medium": 24.0, "low": 12.0}.get(prio, 24.0)
            hours += h
            breakdown[name[:40]] = h

        # Overhead
        hours *= 1.25  # testing + integration
        hours += 16  # project management / setup

        # Clamp to timeline roughly
        max_from_timeline = timeline_weeks * 40 * 0.7  # 0.7 FTE
        if hours > max_from_timeline * 1.5:
            hours = max_from_timeline * 1.2

        total_cost = hours * settings.default_hourly_rate

        return ProjectEstimate(
            total_hours=round(hours, 1),
            total_cost=round(total_cost, 2),
            currency=settings.default_currency,
            breakdown=breakdown,
            confidence="medium" if len(features) >= 3 else "low",
        )
