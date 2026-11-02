"""Tests for the parser shell agent."""

import pytest
from app.shell_agents.parser import ParserAgent


@pytest.mark.asyncio
async def test_parser_basic():
    agent = ParserAgent()
    result = await agent.parse(
        "We need a simple web portal where our customers can log in, view invoices and download PDF statements. Should work on mobile too. We want it in about 8 weeks."
    )
    assert result is not None
    assert hasattr(result, "features") or isinstance(result, dict)
