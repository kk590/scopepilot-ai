"""Tests for deterministic validation rules."""

import pytest
from app.validation.rules import validate_scope_deterministically, detect_repeated_failure


def test_validate_scope_empty():
    # Basic smoke test – adjust once schemas are finalized
    result = validate_scope_deterministically({})
    assert result is not None


def test_detect_repeated_failure():
    history = [{"status": "failed"}, {"status": "failed"}, {"status": "failed"}]
    assert detect_repeated_failure(history) is True
