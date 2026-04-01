from pathlib import Path
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.knowledge import Knowledge
from agno.knowledge.reader.text_reader import TextReader
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.tools import tool

from context import load_context, update_context
from agents.profiles import make_subordinate_tool
from models import build_model_with_fallback, available_providers

_agents: dict[str, Agent] = {}

def _save_context_tool(group_id: str):
    @tool(description="Persist a note or preference to this group's permanent context.")
    def save_to_context(key: str, value: str) -> str:
        update_context(group_id, key, value)
        return f"Saved '{key}'."
    return save_to_context

def get_root_agent(group_id: str, provider_override: str = "") -> Agent:
    cache_key = f"{group_id}:{provider_override}"
    if cache_key in _agents:
        return _agents[cache_key]

    model, used = build_model_with_fallback(
        provider_override or "claude-sonnet",
        ["gpt-4o", "grok-3", "groq-llama", "openrouter-auto"],
    )

    safe_id = group_id.replace(':', '_')

    group_context = load_context(group_id)
    kb_path = Path(f"groups/{safe_id}/knowledge")
    knowledge = None
    if kb_path.exists() and any(kb_path.iterdir()):
        knowledge = Knowledge(
            vector_db=LanceDb(
                uri=f"./lancedb/{safe_id}",
                table_name=f"kb_{safe_id}",
                embedder=OpenAIEmbedder(),
            ),
            readers={"text": TextReader()},
        )

    instructions = [
        "You are a general-purpose personal assistant.",
        "Break complex tasks down. Delegate to sub-agents via call_subordinate.",
        "Check memory first — you may have solved this before.",
        "Synthesise all sub-agent results before replying.",
        f"Active LLM providers: {', '.join(available_providers())}.",
        "You may ask sub-agents to use a specific provider via the provider argument.",
    ]
    if group_context:
        instructions.insert(0, f"Group context:\n{group_context}")
    agent_db = SqliteDb(
        db_file="nanoclaw.db",
        memory_table=f"memory_{safe_id}",
        session_table=f"sessions_{safe_id}",
    )

    agent = Agent(
        name=f"Root [{group_id}] via {used}",
        model=model,
        db=agent_db,
        memory_manager=MemoryManager(db=agent_db),
        knowledge=knowledge,
        tools=[
            make_subordinate_tool(group_id, depth=0),
            _save_context_tool(group_id),
        ],
        enable_agentic_memory=True,
        search_knowledge=knowledge is not None,
        add_history_to_context=True,
        num_history_runs=10,
        instructions=instructions,
        markdown=True,
    )

    _agents[cache_key] = agent
    return agent

def run_for_group(group_id: str, prompt: str, session_id: str, provider: str = "") -> str:
    agent = get_root_agent(group_id, provider_override=provider)
    return agent.run(prompt, session_id=session_id).content or "[no response]"
