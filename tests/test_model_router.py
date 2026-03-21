"""
Tests for the ModelRouter — multi-provider fallback chain validation.

These tests verify:
1. get_llm() returns valid LLMs for all registered agents
2. Unknown agents raise ValueError
3. Provider auto-detection resolves correctly
4. Missing API keys cause graceful chain degradation (not crashes)
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Ensure we can import from src/
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from layer1_core.model_router import (
    ModelRouter,
    AGENT_MODEL_CHAINS,
    _detect_provider,
    _build_single_llm,
)


class TestProviderDetection:
    """Verify that model names auto-resolve to correct providers."""

    def test_openai_detection(self):
        assert _detect_provider("gpt-5-nano") == "openai"
        assert _detect_provider("gpt-4o-mini") == "openai"
        assert _detect_provider("gpt-5.4-mini") == "openai"

    def test_anthropic_detection(self):
        assert _detect_provider("claude-opus-4.6") == "anthropic"
        assert _detect_provider("claude-sonnet-4.6") == "anthropic"
        assert _detect_provider("claude-haiku-4.5") == "anthropic"

    def test_google_detection(self):
        assert _detect_provider("gemini-2.5-flash") == "google"
        assert _detect_provider("gemini-2.5-pro") == "google"
        assert _detect_provider("gemini-2.5-flash-lite") == "google"

    def test_groq_detection(self):
        """Groq hosts Llama and Mixtral models."""
        assert _detect_provider("llama-4-scout") == "groq"
        assert _detect_provider("llama-4-maverick") == "groq"
        assert _detect_provider("mixtral-8x7b") == "groq"

    def test_deepseek_detection(self):
        assert _detect_provider("deepseek-v3.2") == "deepseek"
        assert _detect_provider("deepseek-r1") == "deepseek"

    def test_mistral_detection(self):
        assert _detect_provider("mistral-small-3.1") == "mistral"
        assert _detect_provider("mistral-medium-3.1") == "mistral"

    def test_unknown_falls_to_ollama(self):
        assert _detect_provider("qwen3.5:397b-cloud") == "ollama"
        assert _detect_provider("some-random-model") == "ollama"


class TestModelRouterChainConfig:
    """Verify that all agents are properly configured."""

    # All agents that must exist in the chain config
    REQUIRED_AGENTS = [
        "orchestrator",
        "safety_governor",
        "state_critic",
        "consistency_auditor",
        "auditor_patch",
        "narrative_weaver",
        "chronicler",
        "dna_decoder",
        "history_consensus",
        "lore_extractor",
    ]

    def test_all_agents_registered(self):
        """Every LLM-driven agent must have a chain in AGENT_MODEL_CHAINS."""
        for agent in self.REQUIRED_AGENTS:
            assert agent in AGENT_MODEL_CHAINS, (
                f"Agent '{agent}' missing from AGENT_MODEL_CHAINS"
            )

    def test_each_chain_has_fallbacks(self):
        """Every chain must have at least 2 entries (primary + 1 fallback)."""
        for agent, chain in AGENT_MODEL_CHAINS.items():
            assert len(chain) >= 2, (
                f"Agent '{agent}' has only {len(chain)} model(s) — "
                f"needs at least 2 for fallback resilience."
            )

    def test_chain_entries_are_valid_tuples(self):
        """Each entry must be (model_name, optional_provider_override)."""
        for agent, chain in AGENT_MODEL_CHAINS.items():
            for i, entry in enumerate(chain):
                assert isinstance(entry, tuple) and len(entry) == 2, (
                    f"Agent '{agent}' chain entry {i} is not a valid "
                    f"(model_name, provider_override) tuple: {entry}"
                )
                model_name, provider = entry
                assert isinstance(model_name, str) and len(model_name) > 0, (
                    f"Agent '{agent}' chain entry {i} has invalid model name"
                )


class TestModelRouterGetLLM:
    """Test the get_llm() method behavior."""

    def test_unknown_agent_raises_value_error(self):
        """Requesting an LLM for a non-existent agent must fail clearly."""
        router = ModelRouter()
        with pytest.raises(ValueError, match="Unknown agent"):
            router.get_llm("nonexistent_agent")

    def test_cache_returns_same_instance(self):
        """Repeated calls with same params must return the cached LLM."""
        router = ModelRouter()
        # Use Ollama as fallback (always available)
        with patch.dict(os.environ, {"OLLAMA_API_KEY": "test"}):
            # Mock the _build_single_llm to return a fake LLM
            mock_llm = MagicMock()
            with patch(
                "layer1_core.model_router._build_single_llm",
                return_value=mock_llm
            ):
                llm1 = router.get_llm("orchestrator", temperature=0.1)
                llm2 = router.get_llm("orchestrator", temperature=0.1)
                assert llm1 is llm2  # Same cached instance

    def test_clear_cache(self):
        """clear_cache() must reset the internal cache."""
        router = ModelRouter()
        router._cache["test_key"] = MagicMock()
        assert len(router._cache) == 1
        router.clear_cache()
        assert len(router._cache) == 0


class TestGracefulDegradation:
    """Verify that missing API keys don't crash the system."""

    def test_missing_api_key_returns_none(self):
        """_build_single_llm should return None for providers without keys."""
        # Clear all API keys
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "GOOGLE_API_KEY": "",
        }, clear=False):
            result = _build_single_llm("gpt-5-nano", provider="openai")
            assert result is None

            result = _build_single_llm("claude-opus-4.6", provider="anthropic")
            assert result is None

            result = _build_single_llm("gemini-2.5-flash", provider="google")
            assert result is None

    def test_no_providers_configured_raises_runtime_error(self):
        """If zero providers are available, get_llm must raise RuntimeError."""
        router = ModelRouter()
        # Clear ALL API keys
        clean_env = {k: "" for k in [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "GROQ_API_KEY", "DEEPSEEK_API_KEY", "MISTRAL_API_KEY",
            "OLLAMA_API_KEY",
        ]}
        with patch.dict(os.environ, clean_env, clear=False):
            # Also mock _build_single_llm to always return None
            with patch(
                "layer1_core.model_router._build_single_llm",
                return_value=None
            ):
                with pytest.raises(RuntimeError, match="No LLM providers"):
                    router.get_llm("orchestrator")


class TestFallbackExecution:
    """Simulate primary model failure and verify fallback fires."""

    def test_primary_failure_triggers_fallback(self):
        """
        If the primary model raises an exception, LangChain's
        with_fallbacks should silently route to the next provider.
        """
        router = ModelRouter()

        # Create two mock LLMs
        primary_llm = MagicMock()
        fallback_llm = MagicMock()

        # Primary will simulate a 503 error
        primary_llm.with_fallbacks = MagicMock(return_value="chained_llm")

        with patch(
            "layer1_core.model_router._build_single_llm",
            side_effect=[primary_llm, fallback_llm, None]
        ):
            result = router.get_llm("orchestrator", temperature=0.1)

            # Verify with_fallbacks was called with the secondary
            primary_llm.with_fallbacks.assert_called_once_with([fallback_llm])
            assert result == "chained_llm"
