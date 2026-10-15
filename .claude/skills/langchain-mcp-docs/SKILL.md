---
name: langchain-mcp-docs
description: Consulta la documentación oficial de LangChain con el MCP `docs-langchain` (guías, tutoriales, patrones) ANTES de escribir o modificar cualquier código de LangChain / LangGraph / LangSmith. Se usa SIEMPRE junto con `langchain-mcp-reference` (firmas exactas vía el MCP `reference-langchain`). Use when creating or editing agents, chains, tools, retrievers, RAG pipelines, memory, checkpointers, middleware or graphs; when any file imports langchain, langchain_core, langchain_community, langchain_openai, langgraph or langsmith; when migrating v0 code to v1; or when debugging ImportError / TypeError / deprecation warnings in those packages.
---

# LangChain Docs vía MCP — primero la doc, después el código

La API de LangChain cambia rápido (v0 → v1 movió agentes, prompts y memoria de sitio). El conocimiento del modelo está desactualizado por defecto. **Antes de escribir una sola línea de LangChain se consulta el MCP `docs-langchain`.**

Este proyecto corre en **LangChain 1.x + LangGraph 1.x** (ver `requirements.txt`): `create_agent` de `langchain.agents`, `init_chat_model` de `langchain.chat_models`, checkpointer de LangGraph para memoria. Cualquier snippet de blog/tutorial anterior a v1 es sospechoso hasta verificarlo en la doc.

## Pareja obligatoria: docs + reference

Esta skill y **`langchain-mcp-reference`** se usan **las dos, siempre**, cada vez que se escribe código LangChain:

| Skill | MCP | Responde a |
|---|---|---|
| `langchain-mcp-docs` (esta) | `docs-langchain` | **¿Cómo se hace?** — qué patrón/API usar, ejemplos canónicos |
| `langchain-mcp-reference` | `reference-langchain` | **¿Qué acepta exactamente?** — import, firma, parámetros, tipos |

Orden: primero esta (elegir el patrón), luego `langchain-mcp-reference` (verificar cada símbolo antes de escribirlo).

## Cuándo se dispara

- Crear o editar agentes, tools, chains, retrievers, RAG, memoria, graphs o middleware.
- Tocar `agent.py`, `main_chatwoot.py`, `tools/*.py`, `vector_store.py`, `RAG-Clasico-con-Qdrant/rag.py`, `conversation_history/*.py` o cualquier archivo que importe `langchain*` / `langgraph`.
- "¿Cómo hago X con LangChain?" / "migra esto a la API nueva".
- Debuggear `ModuleNotFoundError`, firmas que no coinciden, o warnings de deprecación.

## Workflow obligatorio

### 1. Traduce la petición a temas de doc

Descompón antes de buscar. No busques "langchain agent" — busca el concepto exacto.

| Petición | Consultas al MCP |
|---|---|
| "agrega una tool al agente" | `create_agent tools`, `@tool decorator`, `tool calling` |
| "que recuerde la conversación" | `checkpointer`, `thread_id`, `persistence postgres` |
| "streaming de la respuesta" | `stream agent`, `stream_mode messages` |
| "structured output" | `response_format`, `structured output agent` |
| "cambiar el system prompt" | `create_agent system_prompt`, `middleware` |
| "esto era `create_react_agent`" | `migrate v0 to v1 agents` |

Si no sabes por dónde entrar, lee [references/topic-map.md](references/topic-map.md).

### 2. Consulta el MCP `docs-langchain`

Dos herramientas, en este orden:

1. **`mcp__docs-langchain__search_docs_by_lang_chain`** — búsqueda semántica. Devuelve títulos + rutas de página.
   ```
   query: "create_agent tools python"
   ```
2. **`mcp__docs-langchain__query_docs_filesystem_docs_by_lang_chain`** — filesystem virtual de solo lectura sobre las páginas `.mdx`. Úsalo para leer la página completa o hacer grep exacto:
   ```
   head -200 /oss/python/langchain/agents.mdx
   rg -il "create_agent" /oss/python/
   tree /oss/python -L 2
   ```
   Cada llamada es *stateless*: usa rutas absolutas, encadena con `&&`.

Reglas de selección de página:
- **Python, no JS.** Este proyecto es Python — filtra rutas `/oss/python/...`, ignora `/oss/javascript/...`.
- Prefiere la página **actual (v1)** sobre cualquier cosa marcada legacy, classic o v0.
- Para agentes/multi-agente/persistencia, la fuente autoritativa suele ser **LangGraph**.

### 3. Verifica cada símbolo con `langchain-mcp-reference`

Por cada clase/función que vayas a usar, confirma con el MCP `reference-langchain` (`get_symbol`):
- **Import exacto** y **paquete** (`langchain`, `langchain-core`, `langgraph`, `langchain-classic`).
- **Firma real** — nombres de parámetros, cuáles son keyword-only, defaults.

Los ejemplos de las guías a veces van un paso por detrás de la referencia: **si discrepan, la firma de `reference-langchain` manda.**

### 4. Di al usuario qué vas a usar (3-5 líneas)

Antes de escribir código:

> Voy a usar `create_agent(model, tools=..., system_prompt=...)` de `langchain.agents` — doc `/oss/python/langchain/agents`, firma verificada en `reference-langchain`. Memoria con `checkpointer` de LangGraph (`/oss/python/langgraph/persistence`), que es lo que ya usa `conversation_history/checkpointer.py`.

### 5. Escribe el código alineado a la doc

- Copia los patrones canónicos antes de improvisar.
- Respeta sync/async tal como aparece en la doc.
- Deja un comentario con la ruta de doc **solo** cuando la decisión no sea obvia:
  ```python
  # Patrón de: /oss/python/langgraph/persistence — thread_id define la sesión
  ```

## Reglas duras

- **Nunca escribas LangChain sin consultar los dos MCPs primero**, aunque "sepas" la respuesta.
- **Si un MCP no responde o el tema no aparece: detente y avisa.** No improvises una API.
- **No mezcles v0 y v1** en el mismo archivo. Si algo solo existe en `langchain-classic`, dilo explícitamente en vez de instalarlo por inercia.
- **No inventes rutas de doc.** Cita solo rutas que el MCP devolvió.
- Si la doc contradice el código existente del proyecto, **señálalo** en vez de reescribir en silencio.

## Contexto adicional

- ¿No sabes qué buscar? → [references/topic-map.md](references/topic-map.md)
- ¿LangChain o LangGraph para esta tarea? → [references/langchain-vs-langgraph.md](references/langchain-vs-langgraph.md)
- ¿Migrando código v0 (AgentExecutor, LLMChain, RetrievalQA, memory)? → [references/migration-checklist.md](references/migration-checklist.md)

## Verificación rápida de que el MCP está disponible

```
mcp__docs-langchain__search_docs_by_lang_chain  query="create_agent"
```
Si la herramienta no existe en la sesión, el MCP `docs-langchain` no está conectado — avisa al usuario antes de continuar (`claude mcp list`).
