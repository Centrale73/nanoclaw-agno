# nanoclaw-agno

A Python framework combining three agent architectures into one system:

- **[Agent Zero](https://github.com/agent0ai/agent-zero)** — dynamic runtime sub-agent spawning, hierarchical delegation, profile-based specialists
- **[NanoClaw](https://github.com/qwibitai/nanoclaw)** — multi-channel ingress (Telegram/Discord/Slack), SQLite message queue, per-group context isolation, scheduled tasks
- **[Agno](https://github.com/agno-agi/agno)** — the Python agent framework handling LLM calls, tool dispatch, memory, knowledge RAG, multi-agent teams

## Core Insight

Agent Zero's `call_subordinate` tool is replicated in Agno by wrapping `Agent()` instantiation inside a `@tool`-decorated function. The root agent calls that tool at runtime, which creates and runs a brand-new Agno agent on the fly. Recursion is bounded by a depth counter closed over in the factory function (max depth 3).

## Architecture

```
Channels (Telegram / Discord / Slack / Scheduler)
        ↓
SQLite message queue  [nanoclaw pattern]
  - per-group queues
  - global concurrency limit
  - message dedup
        ↓
Python asyncio orchestrator  [nanoclaw index.ts → Python]
  - polling loop (0.5s)
  - per-group asyncio.Lock (sequential within a group)
  - global asyncio.Semaphore (MAX_CONCURRENT_AGENTS=4)
        ↓
Root Agno Agent  [Agent Zero pattern]
  - one cached agent per group_id
  - loaded with per-group context (context.md)
  - tools: call_subordinate + save_to_context
  - memory: Agno Memory (SQLite-backed, per group)
  - knowledge: optional RAG over groups/<id>/knowledge/
  - multi-provider: Claude by default, fallback chain
        ↓
Dynamic sub-agents (spawned at runtime via call_subordinate)
  - researcher → Perplexity → Claude → GPT-4o → Groq
  - coder      → Claude → GPT-4o → Groq → DeepSeek
  - analyst    → GPT-4o → Claude → Groq/DeepSeek
  - fast       → Groq-Llama → Claude-Haiku → GPT-4o-mini
  - reasoner   → Claude-Opus → o3 → Grok-3 → DeepSeek
  - realtime   → Grok-3 → Perplexity → Claude
  Sub-agents can themselves spawn further sub-agents (max depth 3)
  Sub-agents share the same per-group Agno Memory instance
        ↓
Response router → back to originating channel
```

## File Structure

```
nanoclaw-agno/
├── orchestrator.py        # main asyncio loop
├── db.py                  # SQLite queue + operations
├── context.py             # per-group context files
├── scheduler.py           # cron-based task runner
├── models.py              # multi-provider registry + fallback builder
├── channels/
│   ├── registry.py        # BaseChannel + self-registration
│   ├── telegram.py
│   ├── discord.py
│   └── slack.py
├── agents/
│   ├── profiles.py        # PROFILES dict + make_subordinate_tool factory
│   └── root.py            # get_root_agent() + run_for_group()
├── groups/
│   └── <group_id>/
│       ├── context.md     # persistent per-group memory/instructions
│       └── knowledge/     # RAG docs for this group
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/qwibitai/nanoclaw-agno.git
cd nanoclaw-agno
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set one LLM provider key + one channel token
```

You only need **one** LLM API key to run. Every other key is optional — the fallback chain skips unavailable providers automatically. OpenRouter as the last fallback means you can reach almost any model with a single key.

### 3. Enable channels

In `orchestrator.py`, uncomment the channels you want:

```python
import channels.telegram   # noqa
# import channels.discord  # noqa
# import channels.slack    # noqa
```

### 4. Run

```bash
python orchestrator.py
```

Or with Docker:

```bash
docker compose up -d
```

## Provider Routing

Each sub-agent profile declares which provider is best for its workload:

| Profile | Primary | Strengths |
|---------|---------|-----------|
| `researcher` | Perplexity (sonar-pro) | Built-in web search |
| `coder` | Claude Sonnet | Best coding output |
| `analyst` | GPT-4o | Vision + data analysis |
| `fast` | Groq (Llama 70B) | Sub-second latency |
| `reasoner` | Claude Opus | Deep multi-step reasoning |
| `realtime` | Grok-3 | Live X/web data |

The root agent receives the `available_providers()` list in its instructions and can explicitly pass a `provider` argument to `call_subordinate` when it has a reason to override.

## Per-Group Isolation

Each `group_id` (e.g. `telegram:123456`) gets:

- Its own SQLite memory table
- Its own `groups/<id>/context.md` (persistent instructions/preferences)
- Its own LanceDB vector store for knowledge RAG
- Its own daily `session_id`

Agents from different groups never share memory.

## Key Design Decisions

1. **Dynamic sub-agent spawning** — `call_subordinate` is created by a factory that closes over `group_id` and `depth`. Recursion bounded by `depth < max_depth`.

2. **Per-group isolation** — the NanoClaw model. Each group is a self-contained context silo.

3. **Provider fallback** — `build_model_with_fallback(preferred, fallbacks)` walks the list and returns the first provider whose API key is set.

4. **One process** — NanoClaw's philosophy. The asyncio event loop runs channels, polling, and scheduler concurrently. Agent runs are offloaded to a thread pool via `run_in_executor`.

## What to Build Next

- [ ] WhatsApp + Gmail channel adapters
- [ ] Container runner: wrap sub-agent execution in Docker containers for filesystem isolation
- [ ] Web UI: Flask + Socket.IO admin panel (active groups, memory, scheduled tasks)
- [ ] `/add-channel` style skill scripts
- [ ] Credential vault: proxy that injects API keys so agents never hold raw credentials
- [ ] Eval harness: benchmark prompts against each provider, score quality/latency

## License

MIT
