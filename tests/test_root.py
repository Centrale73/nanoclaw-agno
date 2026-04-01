"""Test agents/root.py — root agent construction."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set a fake key so root agent can build
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-fake"
os.environ["OPENAI_API_KEY"] = "sk-test-fake"

import context
context.GROUPS_DIR = __import__("pathlib").Path("/tmp/test_groups_root")

from agents.root import get_root_agent, _agents

def cleanup():
    _agents.clear()
    import shutil
    if context.GROUPS_DIR.exists():
        shutil.rmtree(context.GROUPS_DIR)

def test_get_root_agent():
    cleanup()
    agent = get_root_agent("test:root1")
    assert agent is not None
    assert "Root" in agent.name
    assert "test:root1" in agent.name
    print(f"  ✓ get_root_agent creates agent: {agent.name}")

def test_agent_caching():
    agent1 = get_root_agent("test:root1")
    agent2 = get_root_agent("test:root1")
    assert agent1 is agent2, "Same group_id should return cached agent"
    print("  ✓ Same group_id returns cached agent (identity check)")

def test_different_groups_different_agents():
    agent1 = get_root_agent("test:root1")
    agent2 = get_root_agent("test:root2")
    assert agent1 is not agent2, "Different group_ids should give different agents"
    print("  ✓ Different group_ids create separate agents")

def test_provider_override():
    agent_default = get_root_agent("test:override")
    agent_gpt = get_root_agent("test:override", provider_override="gpt-4o")
    # Different cache keys since provider override differs
    assert agent_default is not agent_gpt
    assert "gpt-4o" in agent_gpt.name.lower() or "openai" in str(type(agent_gpt.model)).lower()
    print(f"  ✓ Provider override creates different cached agent: {agent_gpt.name}")

def test_agent_has_tools():
    agent = get_root_agent("test:tools")
    tool_names = [t.__name__ if hasattr(t, '__name__') else str(t) for t in agent.tools]
    assert len(agent.tools) >= 2, f"Expected at least 2 tools, got {len(agent.tools)}: {tool_names}"
    print(f"  ✓ Root agent has {len(agent.tools)} tools: {tool_names}")

def test_agent_has_memory():
    agent = get_root_agent("test:memory")
    assert agent.db is not None, "Root agent should have db configured"
    assert agent.memory_manager is not None, "Root agent should have memory_manager configured"
    print("  ✓ Root agent has db + memory_manager configured")

def test_agent_instructions():
    agent = get_root_agent("test:instr")
    instructions = agent.instructions
    assert any("call_subordinate" in str(i) for i in instructions), "Should mention call_subordinate"
    assert any("provider" in str(i).lower() for i in instructions), "Should mention providers"
    print("  ✓ Root agent instructions include delegation and provider info")

def test_with_group_context():
    context.save_context("test:ctx", "# Custom Context\nThis group prefers French.")
    _agents.clear()  # clear cache to force rebuild
    agent = get_root_agent("test:ctx")
    assert any("French" in str(i) for i in agent.instructions), "Group context should be in instructions"
    print("  ✓ Group context.md injected into agent instructions")

if __name__ == "__main__":
    print("\n=== agents/root.py tests ===")
    test_get_root_agent()
    test_agent_caching()
    test_different_groups_different_agents()
    test_provider_override()
    test_agent_has_tools()
    test_agent_has_memory()
    test_agent_instructions()
    test_with_group_context()
    cleanup()
    print("=== ALL agents/root.py TESTS PASSED ===\n")
