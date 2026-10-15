# Migración de código legacy de LangChain

Carga este archivo cuando estés actualizando código viejo a la API moderna.

## Antes de migrar

1. Identifica qué versión de LangChain tiene el proyecto (`pip show langchain` o `pyproject.toml`).
2. Lista los imports que están deprecados o que se movieron de paquete.
3. **Consulta el MCP** por cada patrón antiguo antes de reescribir.

## Patrones comunes de migración

### `LLMChain` / `Chain` → LCEL

```python
# Antes
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(input="hola")

# Después (LCEL)
chain = prompt | llm
result = chain.invoke({"input": "hola"})
```

### `ConversationChain` / `ConversationBufferMemory` → LangGraph

La memoria viejo-estilo se reemplaza por **state graphs con checkpointers** en LangGraph. Consulta el MCP por:
- `langgraph memory`
- `MessagesState`
- `MemorySaver` / `PostgresSaver` / `SqliteSaver`

### `AgentExecutor` / `create_react_agent` → `create_agent` (v1)

```python
# Antes (deprecated)
from langchain.agents import AgentExecutor, create_react_agent
executor = AgentExecutor(agent=agent, tools=tools)

# Después (recomendado)
from langchain.agents import create_agent
agent = create_agent(model, tools=tools, system_prompt="...")
```

Verifica imports actuales con el MCP — `langgraph.prebuilt` ha cambiado de nombre antes.

### `RetrievalQA` → LCEL custom

```python
# Antes
from langchain.chains import RetrievalQA
qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# Después (esquema, verificar en docs)
from langchain_core.runnables import RunnablePassthrough

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | parser
)
```

### Imports que se movieron de paquete

| Antiguo | Nuevo |
|---|---|
| `from langchain.chat_models import ChatOpenAI` | `from langchain_openai import ChatOpenAI` |
| `from langchain.embeddings import OpenAIEmbeddings` | `from langchain_openai import OpenAIEmbeddings` |
| `from langchain.vectorstores import Pinecone` | `from langchain_pinecone import PineconeVectorStore` |
| `from langchain.tools import tool` | `from langchain_core.tools import tool` |

**Estos cambian seguido — verifica con el MCP cada vez.**

## Checklist al terminar la migración

- [ ] Todos los imports vienen de paquetes específicos (`langchain_openai`, etc.), no del genérico `langchain`.
- [ ] Ningún uso de `Chain.run()` (es legacy) — todo es `.invoke()` o `.stream()`.
- [ ] Memoria de agente usa LangGraph checkpointers, no `ConversationBufferMemory`.
- [ ] Agentes usan LangGraph, no `AgentExecutor`.
- [ ] Verifico que las versiones de los paquetes son compatibles entre sí.
