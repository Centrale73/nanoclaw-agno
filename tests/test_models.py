"""Test models.py — provider registry and fallback logic."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Clear all provider env vars first to test from clean state
for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY",
            "XAI_API_KEY", "PERPLEXITY_API_KEY", "OPENROUTER_API_KEY"]:
    os.environ.pop(key, None)

import models

def test_providers_registry():
    assert len(models.PROVIDERS) >= 18, f"Expected 18+ providers, got {len(models.PROVIDERS)}"
    print(f"  ✓ {len(models.PROVIDERS)} providers registered")

def test_no_providers_available():
    avail = models.available_providers()
    assert avail == [], f"Expected none available, got {avail}"
    print("  ✓ available_providers returns [] when no keys set")

def test_fallback_all_missing():
    try:
        models.build_model_with_fallback("claude-sonnet", ["gpt-4o", "groq-llama"])
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "No available provider" in str(e)
    print("  ✓ build_model_with_fallback raises RuntimeError when all keys missing")

def test_set_one_key():
    os.environ["GROQ_API_KEY"] = "gsk_test_fake_key"
    avail = models.available_providers()
    groq_providers = [p for p in avail if "groq" in p]
    assert len(groq_providers) >= 2, f"Expected groq providers, got {groq_providers}"
    print(f"  ✓ Setting GROQ_API_KEY enables: {groq_providers}")

def test_fallback_skips_to_available():
    # Preferred is claude (unavailable), fallback includes groq-llama (available)
    model, used = models.build_model_with_fallback("claude-sonnet", ["gpt-4o", "groq-llama"])
    assert used == "groq-llama", f"Expected groq-llama, got {used}"
    assert model is not None
    print(f"  ✓ Fallback correctly skipped to '{used}'")

def test_build_model_direct():
    model = models.build_model("groq-llama")
    assert model is not None
    print(f"  ✓ build_model('groq-llama') returns {type(model).__name__}")

def test_build_model_unknown():
    try:
        models.build_model("nonexistent-provider")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown provider" in str(e)
    print("  ✓ build_model raises ValueError for unknown provider")

def test_build_model_unavailable():
    try:
        models.build_model("claude-sonnet")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "requires ANTHROPIC_API_KEY" in str(e)
    print("  ✓ build_model raises RuntimeError for unavailable provider")

def test_providers_with_strength():
    speed = models.providers_with_strength("speed")
    # With only GROQ set, should include groq providers with "speed" strength
    assert any("groq" in p for p in speed), f"Expected groq in speed providers, got {speed}"
    print(f"  ✓ providers_with_strength('speed') = {speed}")

def test_multiple_keys():
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"
    os.environ["OPENAI_API_KEY"] = "sk-test"
    avail = models.available_providers()
    assert "claude-sonnet" in avail
    assert "gpt-4o" in avail
    assert "groq-llama" in avail
    print(f"  ✓ {len(avail)} providers available with 3 keys set")

    # Preferred should now win
    model, used = models.build_model_with_fallback("claude-sonnet", ["gpt-4o", "groq-llama"])
    assert used == "claude-sonnet", f"Expected claude-sonnet, got {used}"
    print(f"  ✓ Preferred provider '{used}' selected when available")

def cleanup():
    for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY",
                "XAI_API_KEY", "PERPLEXITY_API_KEY", "OPENROUTER_API_KEY"]:
        os.environ.pop(key, None)

if __name__ == "__main__":
    print("\n=== models.py tests ===")
    test_providers_registry()
    test_no_providers_available()
    test_fallback_all_missing()
    test_set_one_key()
    test_fallback_skips_to_available()
    test_build_model_direct()
    test_build_model_unknown()
    test_build_model_unavailable()
    test_providers_with_strength()
    test_multiple_keys()
    cleanup()
    print("=== ALL models.py TESTS PASSED ===\n")
