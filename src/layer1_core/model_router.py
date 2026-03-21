"""
ModelRouter — Centralized multi-provider LLM factory with automatic fallback.

Reads agent-to-model mappings from `AGENT_MODEL_CHAINS` and constructs
resilient invocation chains via LangChain's `.with_fallbacks()`.

Usage:
    from layer1_core.model_router import model_router
    llm = model_router.get_llm("orchestrator", temperature=0.1)
"""

import os
import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Provider Detection Constants
# ──────────────────────────────────────────────────────────────────────
# Model name prefixes/substrings → provider mapping
_PROVIDER_PATTERNS = {
    "anthropic": ["claude-", "claude"],
    "openai": ["gpt-", "o1-", "o3-"],
    "google": ["gemini-"],
    "groq": ["llama-", "mixtral-"],
    "deepseek": ["deepseek-"],
    "mistral": ["mistral-", "pixtral-", "codestral-"],
    "ollama": [],  # Fallback for unknown models → assume local Ollama
}

# Environment variable names for each provider's API key
_PROVIDER_API_KEY_ENVS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "ollama": "OLLAMA_API_KEY",
}

# Base URLs for providers that need them
_PROVIDER_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "ollama": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
}

# ──────────────────────────────────────────────────────────────────────
# Agent → Model Fallback Chains (from Compute Matrix §6)
# ──────────────────────────────────────────────────────────────────────
# Each agent maps to an ordered list of (model_name, provider_override).
# provider_override is optional; if None, auto-detected from model name.
AGENT_MODEL_CHAINS: dict[str, list[tuple[str, Optional[str]]]] = {
    "orchestrator": [
        ("gpt-5-nano", None),           # Primary: GPT-5 nano
        ("llama-4-scout", "groq"),       # Fallback 1: Llama 4 Scout on Groq
        ("gemini-2.5-flash-lite", None), # Fallback 2: Gemini Flash-Lite
    ],
    "safety_governor": [
        ("gemini-2.5-flash-lite", None), # Primary: Gemini Flash-Lite
        ("gpt-4o-mini", None),           # Fallback 1: GPT-4o mini
        ("mistral-small-3.1", None),     # Fallback 2: Mistral Small
    ],
    "state_critic": [
        ("llama-4-scout", "groq"),       # Primary: Scout on Groq (fastest)
        ("gpt-5-nano", None),            # Fallback 1: GPT-5 nano
        ("mistral-small-3.1", None),     # Fallback 2: Mistral Small
    ],
    "consistency_auditor": [
        ("gemini-2.5-flash", None),      # Primary: Gemini Flash
        ("claude-haiku-4.5", None),      # Fallback 1: Claude Haiku
        ("deepseek-v3.2", None),         # Fallback 2: DeepSeek V3.2
    ],
    "auditor_patch": [
        ("claude-sonnet-4.6", None),     # Primary: Claude Sonnet (best editing)
        ("mistral-medium-3.1", None),    # Fallback 1: Mistral Medium
        ("gpt-5.4-mini", None),          # Fallback 2: GPT-5.4 mini
    ],
    "narrative_weaver": [
        ("claude-opus-4.6", None),       # Primary: Claude Opus (SOTA prose)
        ("gemini-2.5-pro", None),        # Fallback 1: Gemini Pro
        ("llama-4-maverick", "groq"),    # Fallback 2: Maverick on Groq
    ],
    "chronicler": [
        ("gemini-2.5-flash", None),      # Primary: Gemini Flash
        ("deepseek-v3.2", None),         # Fallback 1: DeepSeek V3.2
        ("mistral-medium-3.1", None),    # Fallback 2: Mistral Medium
    ],
    "dna_decoder": [
        ("claude-opus-4.6", None),       # Primary: Opus (richest profiles)
        ("deepseek-r1", None),           # Fallback 1: DeepSeek R1
        ("llama-4-maverick", "groq"),    # Fallback 2: Maverick on Groq
    ],
    "history_consensus": [
        ("claude-opus-4.6", None),       # Primary: Opus (deep reasoning)
        ("deepseek-r1", None),           # Fallback 1: DeepSeek R1
        ("gemini-2.5-pro", None),        # Fallback 2: Gemini Pro
    ],
    "lore_extractor": [
        ("gemini-2.5-flash", None),      # Primary: Flash (structured extraction)
        ("claude-haiku-4.5", None),      # Fallback 1: Claude Haiku
        ("deepseek-v3.2", None),         # Fallback 2: DeepSeek V3.2
    ],
}


def _detect_provider(model_name: str) -> str:
    """Infer the provider from a model name string."""
    model_lower = model_name.lower()
    for provider, prefixes in _PROVIDER_PATTERNS.items():
        if provider == "ollama":
            continue  # Skip the catch-all
        for prefix in prefixes:
            if model_lower.startswith(prefix):
                return provider
    return "ollama"  # Default: assume local Ollama-compatible endpoint


def _build_single_llm(
    model_name: str,
    provider: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
) -> Optional[BaseChatModel]:
    """
    Construct a single LangChain chat model for the given provider.

    Returns None if the required API key is not configured, allowing
    the caller to silently skip unavailable providers.
    """
    resolved_provider = provider or _detect_provider(model_name)
    api_key_env = _PROVIDER_API_KEY_ENVS.get(resolved_provider, "")
    api_key = os.getenv(api_key_env, "")

    # For non-Ollama providers, require a real API key
    if resolved_provider != "ollama" and not api_key:
        logger.debug(
            f"Skipping {model_name} ({resolved_provider}): "
            f"no {api_key_env} configured."
        )
        return None

    kwargs: dict = {"model": model_name, "temperature": temperature}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    try:
        if resolved_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(api_key=api_key, **kwargs)

        elif resolved_provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                google_api_key=api_key, **kwargs
            )

        elif resolved_provider in ("openai", "groq", "deepseek", "mistral"):
            from langchain_openai import ChatOpenAI

            base_url = _PROVIDER_BASE_URLS.get(resolved_provider)
            extra = {}
            if base_url:
                extra["base_url"] = base_url
            if resolved_provider == "mistral":
                # Mistral uses OpenAI-compatible API at their endpoint
                extra["base_url"] = "https://api.mistral.ai/v1"
            return ChatOpenAI(api_key=api_key, **extra, **kwargs)

        elif resolved_provider == "ollama":
            from langchain_openai import ChatOpenAI

            ollama_key = os.getenv("OLLAMA_API_KEY", "ollama")
            ollama_url = os.getenv(
                "OLLAMA_BASE_URL", "http://localhost:11434/v1"
            )
            return ChatOpenAI(
                api_key=ollama_key, base_url=ollama_url, **kwargs
            )

        else:
            logger.warning(f"Unknown provider '{resolved_provider}' for {model_name}")
            return None

    except ImportError as e:
        logger.warning(
            f"Provider package for {resolved_provider} not installed: {e}. "
            f"Skipping {model_name}."
        )
        return None
    except Exception as e:
        logger.warning(f"Failed to construct {model_name}: {e}")
        return None


class ModelRouter:
    """
    Centralized LLM factory with automatic multi-provider fallback.

    Reads agent names and constructs ordered fallback chains using
    LangChain's `.with_fallbacks()`. If a primary model fails (timeout,
    5xx, rate limit), the chain silently falls through to the next
    provider. The player never sees the failure.
    """

    def __init__(self):
        self._cache: dict[str, BaseChatModel] = {}

    def get_llm(
        self,
        agent_name: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> BaseChatModel:
        """
        Returns a fallback-wrapped LLM for the given agent.

        Args:
            agent_name: Key from AGENT_MODEL_CHAINS (e.g., "orchestrator")
            temperature: LLM temperature override
            max_tokens: Optional token limit (e.g., 100 for StateCritic)

        Returns:
            A BaseChatModel with fallbacks wired.

        Raises:
            ValueError: If agent_name is not in AGENT_MODEL_CHAINS
            RuntimeError: If no providers could be constructed
        """
        cache_key = f"{agent_name}:{temperature}:{max_tokens}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if agent_name not in AGENT_MODEL_CHAINS:
            raise ValueError(
                f"Unknown agent '{agent_name}'. "
                f"Valid agents: {list(AGENT_MODEL_CHAINS.keys())}"
            )

        chain_spec = AGENT_MODEL_CHAINS[agent_name]
        llms: list[BaseChatModel] = []

        for model_name, provider_override in chain_spec:
            llm = _build_single_llm(
                model_name,
                provider=provider_override,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if llm is not None:
                llms.append(llm)

        if not llms:
            raise RuntimeError(
                f"No LLM providers could be configured for agent '{agent_name}'. "
                f"Check your .env file for the required API keys. "
                f"Required chain: {[m for m, _ in chain_spec]}"
            )

        # Wire fallbacks: primary.with_fallbacks([secondary, tertiary, ...])
        if len(llms) == 1:
            result = llms[0]
        else:
            result = llms[0].with_fallbacks(llms[1:])

        self._cache[cache_key] = result
        logger.info(
            f"[ModelRouter] Built chain for '{agent_name}': "
            f"{[m for m, _ in chain_spec[:len(llms)]]}"
        )
        return result

    def clear_cache(self):
        """Clear cached LLM instances. Useful for testing."""
        self._cache.clear()


# ──────────────────────────────────────────────────────────────────────
# Singleton instance — import this in agent modules
# ──────────────────────────────────────────────────────────────────────
model_router = ModelRouter()
