from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.tools import tool
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from models import build_model_with_fallback

PROFILES: dict[str, dict] = {
    "researcher": {
        "description": "Searches the web and synthesises information",
        "preferred_provider": "perplexity",
        "fallback_providers": ["claude-sonnet", "gpt-4o", "groq-llama", "openrouter-gemini"],
        "tools": [DuckDuckGoTools(), Newspaper4kTools()],
        "instructions": [
            "Search thoroughly before answering.",
            "Cross-reference multiple sources.",
            "Return a concise, well-cited summary.",
        ],
    },
    "coder": {
        "description": "Writes and runs Python and shell scripts",
        "preferred_provider": "claude-sonnet",
        "fallback_providers": ["gpt-4o", "groq-llama", "openrouter-deepseek"],
        "tools": [PythonTools(), ShellTools()],
        "instructions": [
            "Write clean, working code.",
            "Always test before reporting results.",
            "Return the output and any created files.",
        ],
    },
    "analyst": {
        "description": "Analyses data and produces charts",
        "preferred_provider": "gpt-4o",
        "fallback_providers": ["claude-sonnet", "groq-deepseek"],
        "tools": [PythonTools()],
        "instructions": ["Produce clear charts and statistics.", "Explain findings in plain language."],
    },
    "fast": {
        "description": "Quick answers — low latency, cheap",
        "preferred_provider": "groq-llama",
        "fallback_providers": ["claude-haiku", "gpt-4o-mini", "grok-3-mini", "openrouter-auto"],
        "tools": [],
        "instructions": ["Answer concisely and quickly."],
    },
    "reasoner": {
        "description": "Deep reasoning, complex multi-step problems",
        "preferred_provider": "claude-opus",
        "fallback_providers": ["o3", "grok-3", "groq-deepseek", "openrouter-deepseek"],
        "tools": [],
        "instructions": ["Think step by step.", "Show full reasoning before conclusion."],
    },
    "realtime": {
        "description": "Tasks requiring up-to-the-minute information",
        "preferred_provider": "grok-3",
        "fallback_providers": ["perplexity", "claude-sonnet"],
        "tools": [DuckDuckGoTools()],
        "instructions": [
            "Prioritise the most recent information available.",
            "Clearly state the date of any facts you retrieve.",
        ],
    },
}

def make_subordinate_tool(group_id: str, depth: int, max_depth: int = 3):
    """
    Returns a call_subordinate tool bound to this group.
    The tool factory closes over group_id and depth, enabling
    recursive spawning up to max_depth levels.
    """
    safe_id = group_id.replace(':', '_')
    shared_db = SqliteDb(
        db_file="nanoclaw.db",
        memory_table=f"memory_{safe_id}",
        session_table=f"sessions_{safe_id}",
    )
    shared_memory_manager = MemoryManager(db=shared_db)
    available = list(PROFILES.keys())

    @tool(
        description=(
            f"Spawn a specialised sub-agent at runtime. Profiles: {', '.join(available)}. "
            "Optionally override provider (e.g. 'groq-llama' for speed, 'claude-opus' for depth). "
            "Leave provider empty to use profile default."
        )
    )
    def call_subordinate(profile: str, task: str, provider: str = "") -> str:
        """
        Args:
            profile:  One of the registered agent profiles.
            task:     Self-contained description of the subtask.
            provider: Optional provider override.
        """
        config = PROFILES.get(profile, {
            "description": "General assistant",
            "preferred_provider": "claude-sonnet",
            "fallback_providers": ["gpt-4o", "groq-llama"],
            "tools": [],
            "instructions": ["You are a general-purpose assistant."],
        })

        if provider:
            model, used = build_model_with_fallback(provider, config["fallback_providers"])
        else:
            model, used = build_model_with_fallback(
                config["preferred_provider"], config["fallback_providers"]
            )

        child_tools = list(config["tools"])
        if depth < max_depth:
            child_tools.append(make_subordinate_tool(group_id, depth + 1, max_depth))

        child = Agent(
            name=f"{profile}/{used} (depth {depth+1})",
            model=model,
            tools=child_tools,
            db=shared_db,
            memory_manager=shared_memory_manager,
            enable_agentic_memory=True,
            instructions=config["instructions"],
            markdown=False,
        )

        return child.run(task).content or "[no output]"

    return call_subordinate
