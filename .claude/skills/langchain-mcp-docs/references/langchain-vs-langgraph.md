# LangChain vs LangGraph — Cuándo usar cada uno

Carga este archivo solo cuando haya duda sobre qué librería elegir.

## Regla general

A partir del rediseño de la API:

- **LangGraph** = orquestación de **agentes, workflows con estado, multi-agent, control de flujo complejo, checkpointing**.
- **LangChain (core)** = primitives (chat models, embeddings, vectorstores, document loaders, output parsers) y **composición simple con LCEL**.
- **LangSmith** = observabilidad y evaluación (tracing, evals, prompts).

## Tabla de decisión rápida

| Tarea | Usa |
|---|---|
| Un único LLM call con prompt + parsing | LangChain (LCEL) |
| Chain lineal (prompt → LLM → parser) | LangChain (LCEL) |
| RAG simple | LangChain (retrievers + LCEL) |
| Agent con tool-calling | **LangChain v1** (`create_agent` de `langchain.agents`) |
| Multi-agent (supervisor, handoffs) | **LangGraph** |
| Workflow con loops, branches, human-in-the-loop | **LangGraph** |
| Memoria persistente entre sesiones | **LangGraph** (checkpointers) |
| Streaming de tokens | Ambos lo soportan; LCEL si es chain, LangGraph si es agent |

## Cosas que la gente todavía usa pero ya no son recomendadas

| Antiguo | Nuevo |
|---|---|
| `AgentExecutor`, `initialize_agent`, `create_react_agent` | `create_agent` (`langchain.agents`) |
| `ConversationChain`, `ConversationBufferMemory` | LangGraph con `MessagesState` + checkpointer |
| `RetrievalQA`, `ConversationalRetrievalChain` | LCEL chain custom o LangGraph |
| `LLMChain` | LCEL: `prompt | llm | parser` |

## Cuándo verificar con el MCP de todas formas

Aunque la tabla anterior orienta, **siempre verifica en docs** porque:
- Las APIs siguen evolucionando.
- Los nombres de helpers (`create_react_agent` vs `create_agent` vs otros) cambian entre versiones.
- Los imports se reorganizan entre `langchain`, `langchain_core`, `langgraph.prebuilt`, etc.
