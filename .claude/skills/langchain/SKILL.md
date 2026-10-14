---
name: langchain
description: Use when building AI agents, workflows, and applications that call
  LLMs and tools. Reach for this skill when implementing agents with tool
  calling, memory, streaming, multi-agent systems, or deploying to production
  with LangSmith.
metadata:
  mintlify-proj: langchain
  version: "1.0"
---

# LangChain Skill

## Product summary

LangChain is a framework for building AI agents and applications that call language models and tools in loops until tasks complete. It provides abstractions for models, tools, agents, and middleware that compose into production-ready systems. Key files and commands: install with `pip install langchain` or `uv add langchain`; import `create_agent` from `langchain.agents`; configure models with `init_chat_model()` and provider strings like `"openai:gpt-4"` or `"claude-sonnet-4-6"`; define tools with the `@tool` decorator; add memory with checkpointers from `langgraph.checkpoint`; trace with LangSmith by setting `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`. Primary docs: https://docs.langchain.com/oss/python/langchain/overview

## When to use

Use LangChain when:
- Building agents that call tools in loops (weather agents, research assistants, data analyzers)
- Integrating multiple LLM providers (OpenAI, Anthropic, Google, Bedrock, etc.) with a unified interface
- Adding memory and conversation history to agents
- Implementing multi-agent systems with subagents and handoffs
- Streaming agent responses to users in real time
- Deploying agents to production with LangSmith
- Needing middleware for fault tolerance, retries, guardrails, or human-in-the-loop approval
- Working with structured outputs and tool calling
- Building RAG (retrieval-augmented generation) systems

Do not use LangChain for: low-level graph orchestration (use LangGraph directly), simple prompt-only applications without tools, or when you need maximum control over every execution step (use LangGraph).

## Quick reference

### Essential imports and setup

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
```

### Model initialization patterns

| Provider | Model String | Setup |
|----------|--------------|-------|
| OpenAI | `"openai:gpt-4"` | Set `OPENAI_API_KEY` |
| Claude (Anthropic) | `"claude-sonnet-4-6"` | Set `ANTHROPIC_API_KEY` |
| Google Gemini | `"google_genai:gemini-2.5-flash-lite"` | Set `GOOGLE_API_KEY` |
| AWS Bedrock | `"bedrock_converse:us.anthropic.claude-sonnet-4-6"` | Set AWS credentials |
| Azure OpenAI | `"azure_openai:gpt-4"` | Set `AZURE_OPENAI_*` vars |
| Ollama (local) | `"ollama:devstral-2"` | Run Ollama locally |

### Creating agents

```python
# Minimal agent
agent = create_agent(
    model="openai:gpt-4",
    tools=[my_tool],
    system_prompt="You are helpful"
)

# With memory and configuration
agent = create_agent(
    model=init_chat_model("gpt-4", temperature=0.5, max_tokens=2000),
    tools=[tool1, tool2],
    system_prompt="...",
    checkpointer=InMemorySaver(),  # For conversation history
)
```

### Invoking agents

```python
# Single turn
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})

# With thread_id for persistent memory
result = agent.invoke(
    {"messages": [{"role": "user", "content": "..."}]},
    config={"configurable": {"thread_id": "user-123"}}
)

# With streaming
for event in agent.stream({"messages": [...]}, config={"configurable": {"thread_id": "..."}}, stream_mode="updates"):
    print(event)
```

### Defining tools

```python
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city. Use this when user asks about weather."""
    return f"Sunny in {city}"

# Or pass any callable
def calculate(x: int, y: int) -> int:
    return x + y

agent = create_agent(model="...", tools=[get_weather, calculate])
```

### Common middleware patterns

| Middleware | Purpose | Import |
|-----------|---------|--------|
| `ModelRetryMiddleware` | Retry model calls on failure | `langchain.agents.middleware.model_retry` |
| `ToolRetryMiddleware` | Retry tool calls on failure | `langchain.agents.middleware.tool_retry` |
| `SummarizationMiddleware` | Compress history when context fills | `langchain.agents.middleware.summarization` |
| `PIIMiddleware` | Detect and mask PII | `langchain.agents.middleware.pii` |
| `HumanInTheLoopMiddleware` | Pause for human approval | `langchain.agents.middleware.human_in_the_loop` |

## Decision guidance

### When to use `create_agent` vs `create_deep_agent`

| Aspect | `create_agent` | `create_deep_agent` |
|--------|---|---|
| **Setup** | Minimal, configure what you need | Pre-assembled with planning, filesystem, subagents |
| **Use case** | Simple tools, fine-grained control | Complex research, coding, file operations |
| **Memory** | Manual checkpointer setup | Filesystem-backed memory included |
| **Subagents** | Add via middleware | Built-in delegation support |
| **When to choose** | You know exactly what you need | You want batteries-included capabilities |

### When to use LangChain agents vs LangGraph

| Aspect | LangChain agents | LangGraph |
|--------|---|---|
| **Abstraction level** | High-level, opinionated | Low-level, flexible |
| **Tool calling loop** | Built-in, automatic | You define the loop |
| **Deterministic steps** | Limited | Mix deterministic + agentic freely |
| **When to choose** | Standard agent patterns | Custom workflows, precise control |

### When to use checkpointers

| Checkpointer | Use case | Persistence |
|---|---|---|
| `InMemorySaver()` | Local development, testing | In-process memory only |
| `PostgresSaver()` | Production, multi-process | Postgres database |
| `RedisSaver()` | High-throughput production | Redis cache |
| `SqliteSaver()` | Single-machine production | SQLite file |

## Workflow

1. **Understand the task**: Identify what the agent needs to do, what tools it needs, and what model capabilities are required (tool calling, structured output, etc.).

2. **Choose a model**: Pick a provider and model string. Set the required API key. Test with `init_chat_model()` if you need custom parameters.

3. **Define tools**: Write functions decorated with `@tool` or pass callables. Include clear docstrings—they become part of the model's prompt. Test tools independently first.

4. **Write the system prompt**: Be specific about the agent's role, capabilities, and constraints. Include examples if the task is complex.

5. **Create the agent**: Call `create_agent()` with model, tools, and prompt. Add a checkpointer if you need memory across turns.

6. **Test locally**: Invoke with sample inputs. Stream responses to see intermediate steps. Check tool calls in LangSmith traces.

7. **Add middleware as needed**: Start simple. Add retries, summarization, or guardrails only when you hit specific problems.

8. **Deploy**: Use LangSmith Cloud for managed infrastructure, or deploy to your own infrastructure with a checkpointer backed by Postgres or Redis.

9. **Monitor**: Trace all runs with LangSmith. Set up LangSmith Engine to detect issues and propose fixes.

## Common gotchas

- **Forgetting to set API keys**: Model initialization fails silently if `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. are not set. Always check environment variables first.

- **Tools without docstrings**: The model can't see what a tool does if it has no docstring. Always include a clear description in the `@tool` decorator or function docstring.

- **Checkpointer not configured**: Without a checkpointer, `thread_id` is ignored and conversation history is lost between invocations. Always pass `checkpointer=` to `create_agent()` if you need memory.

- **Model string format wrong**: Use `"provider:model"` (e.g., `"openai:gpt-4"`), not just `"gpt-4"`. Check the provider integration docs for exact format.

- **Streaming without proper event handling**: `stream()` returns events, not final results. Always iterate through events and check the event type before accessing data.

- **Context window overflow**: Long conversations fill the context window. Use `SummarizationMiddleware` to compress history, or implement your own summarization logic.

- **Tool results too large**: If a tool returns megabytes of data, the model can't process it. Truncate or summarize large results before returning from tools.

- **Forgetting to handle tool errors**: Tools can fail. Return error messages as strings, not exceptions. The agent will see the error and can retry or ask for clarification.

- **Not testing tools independently**: Always test tools in isolation before adding them to an agent. Mock external APIs if needed.

- **Mixing LangChain and LangGraph APIs**: Don't try to use LangGraph's low-level graph API inside a LangChain agent. Use one or the other, or use LangChain agents on top of LangGraph.

## Verification checklist

Before submitting agent code:

- [ ] All required API keys are set (check with `os.getenv()`)
- [ ] Model string is in correct format (`"provider:model"`)
- [ ] All tools have clear docstrings describing what they do
- [ ] Tools are tested independently and handle errors gracefully
- [ ] System prompt is specific and includes examples if needed
- [ ] Checkpointer is configured if memory is required
- [ ] Agent invocation includes `thread_id` if using persistent memory
- [ ] Streaming is tested if using `stream()` mode
- [ ] LangSmith tracing is enabled for debugging (`LANGSMITH_TRACING=true`)
- [ ] Middleware is added only for specific problems (retries, summarization, etc.)
- [ ] Tool results are truncated or summarized if they're large
- [ ] Error handling in tools returns strings, not exceptions
- [ ] Agent behavior is tested with sample inputs before deployment

## Resources

**Comprehensive navigation**: https://docs.langchain.com/llms.txt

**Critical documentation pages**:
1. [LangChain Quickstart](https://docs.langchain.com/oss/python/langchain/quickstart) — Build your first agent in minutes
2. [Agents](https://docs.langchain.com/oss/python/langchain/agents) — Core agent concepts, tools, middleware, and configuration
3. [Models](https://docs.langchain.com/oss/python/langchain/models) — Model initialization, provider setup, and capabilities

---

> For additional documentation and navigation, see: https://docs.langchain.com/llms.txt
