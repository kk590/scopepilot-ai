"""Deterministic validation rules for scopes."""

from __future__ import annotations

from typing import Any


def validate_scope_deterministically(scope: dict[str, Any]) -> dict[str, Any]:
    """Run pure-Python checks that do not require an LLM."""
    issues = []
    ok = True

    if not scope.get("summary") or len(str(scope.get("summary", "")).strip()) < 20:
        issues.append("Summary is missing or too short")
        ok = False

    features = scope.get("features") or []
    if len(features) < 1:
        issues.append("At least one feature is required")
        ok = False

    for i, f in enumerate(features):
        if isinstance(f, dict):
            name = f.get("name") or ""
            desc = f.get("description") or ""
        else:
            name = getattr(f, "name", "")
            desc = getattr(f, "description", "")
        if not name or len(name) < 3:
            issues.append(f"Feature {i+1} has no usable name")
            ok = False
        if not desc or len(desc) < 10:
            issues.append(f"Feature '{name}' has insufficient description")
            ok = False

    timeline = scope.get("timeline_weeks")
    if timeline is not None:
        try:
            t = int(timeline)
            if t < 1 or t > 104:
                issues.append("Timeline (weeks) looks unrealistic")
                ok = False
        except (TypeError, ValueError):
            issues.append("Timeline is not a valid number")
            ok = False

    return {"ok": ok, "issues": issues}


def detect_repeated_failure(history: list[dict[str, Any]], threshold: int = 3) -> bool:
    """Return True if the last `threshold` verification attempts all failed."""
    if len(history) < threshold:
        return False
    recent = history[-threshold:]
    return all(not h.get("verified", False) for h in recent)
