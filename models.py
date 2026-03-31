import os
from dataclasses import dataclass, field
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.models.groq import Groq
from agno.models.xai import xAI
from agno.models.openrouter import OpenRouter
from agno.models.openai.like import OpenAILike

@dataclass
class ProviderConfig:
    name: str
    model_id: str
    env_key: str
    strengths: list[str] = field(default_factory=list)
    context_window: int = 128_000
    supports_tools: bool = True

PROVIDERS: dict[str, ProviderConfig] = {
    # Anthropic
    "claude-sonnet":       ProviderConfig("claude-sonnet",       "claude-sonnet-4-6",              "ANTHROPIC_API_KEY",    ["reasoning","coding","long-context"], 200_000),
    "claude-haiku":        ProviderConfig("claude-haiku",        "claude-haiku-4-5-20251001",      "ANTHROPIC_API_KEY",    ["speed","cheap"], 200_000),
    "claude-opus":         ProviderConfig("claude-opus",         "claude-opus-4-6",                "ANTHROPIC_API_KEY",    ["complex-reasoning","research"], 200_000),
    # OpenAI
    "gpt-4o":              ProviderConfig("gpt-4o",              "gpt-4o",                         "OPENAI_API_KEY",       ["vision","coding","general"], 128_000),
    "gpt-4o-mini":         ProviderConfig("gpt-4o-mini",         "gpt-4o-mini",                    "OPENAI_API_KEY",       ["speed","cheap"], 128_000),
    "o3":                  ProviderConfig("o3",                  "o3",                             "OPENAI_API_KEY",       ["deep-reasoning","math"], 200_000),
    "o4-mini":             ProviderConfig("o4-mini",             "o4-mini",                        "OPENAI_API_KEY",       ["reasoning","speed"], 200_000),
    # Groq
    "groq-llama":          ProviderConfig("groq-llama",          "llama-3.3-70b-versatile",        "GROQ_API_KEY",         ["speed","cheap","general"], 32_768),
    "groq-llama-8b":       ProviderConfig("groq-llama-8b",       "llama3-8b-8192",                 "GROQ_API_KEY",         ["speed","cheap","simple-tasks"], 8_192),
    "groq-deepseek":       ProviderConfig("groq-deepseek",       "deepseek-r1-distill-llama-70b",  "GROQ_API_KEY",         ["reasoning","speed"], 32_768),
    # xAI / Grok
    "grok-3":              ProviderConfig("grok-3",              "grok-3",                         "XAI_API_KEY",          ["reasoning","real-time","general"], 131_072),
    "grok-3-mini":         ProviderConfig("grok-3-mini",         "grok-3-mini",                    "XAI_API_KEY",          ["speed","cheap"], 131_072),
    # Perplexity
    "perplexity":          ProviderConfig("perplexity",          "sonar-pro",                      "PERPLEXITY_API_KEY",   ["web-search","research","real-time"], 127_072, supports_tools=False),
    "perplexity-fast":     ProviderConfig("perplexity-fast",     "sonar",                          "PERPLEXITY_API_KEY",   ["web-search","speed"], 127_072, supports_tools=False),
    # OpenRouter
    "openrouter-auto":     ProviderConfig("openrouter-auto",     "openrouter/auto",                "OPENROUTER_API_KEY",   ["general","routing"]),
    "openrouter-gemini":   ProviderConfig("openrouter-gemini",   "google/gemini-2.0-flash-001",    "OPENROUTER_API_KEY",   ["speed","vision","long-context"], 1_048_576),
    "openrouter-mistral":  ProviderConfig("openrouter-mistral",  "mistralai/mistral-large-2411",   "OPENROUTER_API_KEY",   ["coding","european-data-residency"]),
    "openrouter-deepseek": ProviderConfig("openrouter-deepseek", "deepseek/deepseek-r1",           "OPENROUTER_API_KEY",   ["reasoning","cheap"]),
}

def _is_available(cfg: ProviderConfig) -> bool:
    return bool(os.environ.get(cfg.env_key))

def build_model(provider_key: str):
    cfg = PROVIDERS.get(provider_key)
    if not cfg:
        raise ValueError(f"Unknown provider '{provider_key}'")
    if not _is_available(cfg):
        raise RuntimeError(f"Provider '{provider_key}' requires {cfg.env_key}")
    mid = cfg.model_id
    if cfg.env_key == "ANTHROPIC_API_KEY":   return Claude(id=mid)
    if cfg.env_key == "OPENAI_API_KEY":       return OpenAIChat(id=mid)
    if cfg.env_key == "GROQ_API_KEY":         return Groq(id=mid)
    if cfg.env_key == "XAI_API_KEY":          return xAI(id=mid)
    if cfg.env_key == "PERPLEXITY_API_KEY":
        return OpenAILike(id=mid, base_url="https://api.perplexity.ai",
                          api_key=os.environ["PERPLEXITY_API_KEY"])
    if cfg.env_key == "OPENROUTER_API_KEY":   return OpenRouter(id=mid)
    raise ValueError(f"No builder for {cfg.env_key}")

def build_model_with_fallback(preferred: str, fallbacks: list[str]):
    """Returns (model, provider_key_used). Skips unavailable keys."""
    for key in [preferred] + fallbacks:
        cfg = PROVIDERS.get(key)
        if cfg and _is_available(cfg):
            return build_model(key), key
    raise RuntimeError(f"No available provider in chain: {[preferred]+fallbacks}")

def available_providers() -> list[str]:
    return [k for k, cfg in PROVIDERS.items() if _is_available(cfg)]

def providers_with_strength(strength: str) -> list[str]:
    return [k for k, cfg in PROVIDERS.items()
            if strength in cfg.strengths and _is_available(cfg)]
