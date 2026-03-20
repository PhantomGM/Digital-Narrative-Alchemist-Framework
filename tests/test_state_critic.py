"""
Unit tests for Phase 2 Bucket I — State Critic Circuit Breaker.

Tests the StateCritic.validate() method with mocked LLM responses
to verify it correctly identifies matches and mismatches between
narrative prose and mechanical deltas.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from agents.layer3_support.state_critic import StateCritic


@pytest.fixture
def critic():
    """Create a StateCritic with a mocked LLM."""
    with patch('agents.layer3_support.state_critic.ChatOpenAI'):
        c = StateCritic()
        c.chain = MagicMock()
        return c


class TestStateCriticMatch:
    """Tests where prose correctly matches the mechanical truth."""

    def test_match_returns_consistent(self, critic):
        critic.chain.ainvoke = AsyncMock(return_value="MATCH")

        result = asyncio.get_event_loop().run_until_complete(
            critic.validate(
                prose="Your blade strikes true, dealing a devastating blow.",
                mechanical_delta={"success": True, "damage": 8}
            )
        )

        assert result["is_consistent"] is True
        assert result["mismatch_detail"] == ""

    def test_empty_prose_defaults_to_consistent(self, critic):
        result = asyncio.get_event_loop().run_until_complete(
            critic.validate(prose="", mechanical_delta={"success": True})
        )
        assert result["is_consistent"] is True

    def test_empty_delta_defaults_to_consistent(self, critic):
        result = asyncio.get_event_loop().run_until_complete(
            critic.validate(prose="Some prose.", mechanical_delta={})
        )
        assert result["is_consistent"] is True


class TestStateCriticMismatch:
    """Tests where prose contradicts the mechanical truth."""

    def test_mismatch_returns_inconsistent(self, critic):
        critic.chain.ainvoke = AsyncMock(
            return_value="MISMATCH | Prose describes failure but Arbiter says success"
        )

        result = asyncio.get_event_loop().run_until_complete(
            critic.validate(
                prose="Your sword bounces harmlessly off the armor.",
                mechanical_delta={"success": True, "damage": 8}
            )
        )

        assert result["is_consistent"] is False
        assert "failure" in result["mismatch_detail"]

    def test_mismatch_without_pipe_separator(self, critic):
        critic.chain.ainvoke = AsyncMock(
            return_value="MISMATCH the prose says miss but math says hit"
        )

        result = asyncio.get_event_loop().run_until_complete(
            critic.validate(
                prose="You miss entirely.",
                mechanical_delta={"success": True}
            )
        )

        assert result["is_consistent"] is False
        # Without pipe, full response is the detail
        assert "miss" in result["mismatch_detail"]


class TestStateCriticErrorHandling:
    """Tests for graceful error handling."""

    def test_llm_error_defaults_to_consistent(self, critic):
        critic.chain.ainvoke = AsyncMock(side_effect=Exception("LLM timeout"))

        result = asyncio.get_event_loop().run_until_complete(
            critic.validate(
                prose="Some narrative prose.",
                mechanical_delta={"success": True}
            )
        )

        assert result["is_consistent"] is True
        assert result["mismatch_detail"] == ""
