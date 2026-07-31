"""
Unit tests for Phase 2 Bucket I — State Critic Circuit Breaker.

Tests the StateCritic.validate() method with mocked LLM responses
to verify it correctly identifies matches and mismatches between
narrative prose and mechanical deltas.

The fixture previously patched state_critic.ChatOpenAI, a name the module
imported but never used — construction had moved to model_router.get_llm(), so
the patch intercepted nothing and every test errored building real providers.
Tests also drove coroutines with asyncio.get_event_loop().run_until_complete(),
which no longer works on Python 3.14.
"""

import io
import os
import sys

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer3_operations.state_critic import StateCritic  # noqa: E402

pytestmark = pytest.mark.anyio


@pytest.fixture
def critic():
    """A StateCritic with no real model behind it."""
    with patch("layer1_core.model_router.model_router.get_llm",
               return_value=MagicMock()):
        c = StateCritic()
    c.chain = MagicMock()
    return c


class TestStateCriticMatch:
    """Tests where prose correctly matches the mechanical truth."""

    async def test_match_returns_consistent(self, critic):
        critic.chain.ainvoke = AsyncMock(return_value="MATCH")

        result = await critic.validate(
            prose="Your blade strikes true, dealing a devastating blow.",
            mechanical_delta={"success": True, "damage": 8},
        )

        assert result["is_consistent"] is True
        assert result["mismatch_detail"] == ""

    async def test_empty_prose_defaults_to_consistent(self, critic):
        result = await critic.validate(prose="", mechanical_delta={"success": True})
        assert result["is_consistent"] is True

    async def test_empty_delta_defaults_to_consistent(self, critic):
        result = await critic.validate(prose="Some prose.", mechanical_delta={})
        assert result["is_consistent"] is True

    async def test_short_circuit_skips_the_model(self, critic):
        critic.chain.ainvoke = AsyncMock(return_value="MISMATCH | never called")
        await critic.validate(prose="   ", mechanical_delta={"success": True})
        critic.chain.ainvoke.assert_not_awaited()

    async def test_surrounding_whitespace_is_tolerated(self, critic):
        critic.chain.ainvoke = AsyncMock(return_value="  MATCH\n")
        result = await critic.validate(prose="Prose.", mechanical_delta={"ok": 1})
        assert result["is_consistent"] is True


class TestStateCriticMismatch:
    """Tests where prose contradicts the mechanical truth."""

    async def test_mismatch_returns_inconsistent(self, critic):
        critic.chain.ainvoke = AsyncMock(
            return_value="MISMATCH | Prose describes failure but Arbiter says success"
        )

        result = await critic.validate(
            prose="Your sword bounces harmlessly off the armor.",
            mechanical_delta={"success": True, "damage": 8},
        )

        assert result["is_consistent"] is False
        assert "failure" in result["mismatch_detail"]

    async def test_mismatch_without_pipe_separator(self, critic):
        critic.chain.ainvoke = AsyncMock(
            return_value="MISMATCH the prose says miss but math says hit"
        )

        result = await critic.validate(
            prose="You miss entirely.",
            mechanical_delta={"success": True},
        )

        assert result["is_consistent"] is False
        # Without pipe, full response is the detail
        assert "miss" in result["mismatch_detail"]

    async def test_mismatch_detail_is_reported_on_a_cp1252_stdout(self, critic, monkeypatch):
        """
        A verdict must not depend on whether it can be logged.

        The mismatch log used a non-ASCII glyph and sat inside the same try that
        fell back to "consistent". On a piped Windows stdout (cp1252) the print
        raised UnicodeEncodeError, and a real mismatch was reported as a match —
        the circuit breaker failing open silently.
        """
        monkeypatch.setattr(
            sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))

        critic.chain.ainvoke = AsyncMock(return_value="MISMATCH | prose says miss")
        result = await critic.validate(
            prose="You miss.", mechanical_delta={"success": True})

        assert result["is_consistent"] is False
        assert "miss" in result["mismatch_detail"]


class TestStateCriticErrorHandling:
    """Tests for graceful error handling."""

    async def test_llm_error_defaults_to_consistent(self, critic):
        critic.chain.ainvoke = AsyncMock(side_effect=Exception("LLM timeout"))

        result = await critic.validate(
            prose="Some narrative prose.",
            mechanical_delta={"success": True},
        )

        assert result["is_consistent"] is True
        assert result["mismatch_detail"] == ""

    async def test_empty_model_response_is_not_a_match(self, critic):
        """An empty reply is not the literal "MATCH" the prompt demands."""
        critic.chain.ainvoke = AsyncMock(return_value="")
        result = await critic.validate(
            prose="Prose.", mechanical_delta={"success": True})
        assert result["is_consistent"] is False

    async def test_none_response_does_not_raise(self, critic):
        critic.chain.ainvoke = AsyncMock(return_value=None)
        result = await critic.validate(
            prose="Prose.", mechanical_delta={"success": True})
        assert result["is_consistent"] is False
