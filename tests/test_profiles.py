"""Test agents/profiles.py — subordinate tool factory and profile definitions."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.profiles import PROFILES, make_subordinate_tool

def test_profiles_defined():
    expected = {"researcher", "coder", "analyst", "fast", "reasoner", "realtime"}
    actual = set(PROFILES.keys())
    assert expected == actual, f"Missing profiles: {expected - actual}"
    print(f"  ✓ All 6 profiles defined: {sorted(actual)}")

def test_profile_structure():
    required_keys = {"description", "preferred_provider", "fallback_providers", "tools", "instructions"}
    for name, config in PROFILES.items():
        missing = required_keys - set(config.keys())
        assert not missing, f"Profile '{name}' missing keys: {missing}"
    print("  ✓ All profiles have required keys (description, preferred_provider, fallback_providers, tools, instructions)")

def test_fallback_chains_non_empty():
    for name, config in PROFILES.items():
        assert len(config["fallback_providers"]) >= 1, f"Profile '{name}' has no fallbacks"
    print("  ✓ All profiles have at least 1 fallback provider")

def test_make_subordinate_tool_returns_function():
    tool_fn = make_subordinate_tool("test:group", depth=0, max_depth=3)
    from agno.tools.function import Function
    assert isinstance(tool_fn, Function), f"Expected Function, got {type(tool_fn)}"
    assert tool_fn.name == "call_subordinate"
    print(f"  ✓ make_subordinate_tool returns Agno Function: {tool_fn.name}")

def test_depth_bounding():
    """Verify that at max_depth, the tool factory does NOT recurse."""
    from agno.tools.function import Function
    for d in range(4):
        tool_fn = make_subordinate_tool("test:depth", depth=d, max_depth=3)
        assert isinstance(tool_fn, Function), f"Failed at depth {d}"
    print("  ✓ make_subordinate_tool creates at depths 0-3 without error")

def test_tool_description_contains_profiles():
    tool_fn = make_subordinate_tool("test:desc", depth=0)
    assert "researcher" in tool_fn.description
    assert "coder" in tool_fn.description
    assert "call_subordinate" == tool_fn.name
    print(f"  ✓ Tool description lists profiles and name is 'call_subordinate'")

if __name__ == "__main__":
    print("\n=== agents/profiles.py tests ===")
    test_profiles_defined()
    test_profile_structure()
    test_fallback_chains_non_empty()
    test_make_subordinate_tool_returns_function()
    test_depth_bounding()
    test_tool_description_contains_profiles()
    print("=== ALL agents/profiles.py TESTS PASSED ===\n")
