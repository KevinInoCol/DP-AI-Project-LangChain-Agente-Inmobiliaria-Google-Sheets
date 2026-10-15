---
name: langchain-mcp-reference
description: Verifica en la referencia oficial de la API de LangChain, con el MCP `reference-langchain` (search_api / get_symbol), el import exacto, el paquete, la firma y los parámetros de CADA clase o función de LangChain / LangGraph / LangSmith ANTES de escribirla. Se usa SIEMPRE junto con `langchain-mcp-docs` (guías vía el MCP `docs-langchain`). Use when writing, refactoring, reviewing or debugging code that imports langchain, langchain_core, langchain_openai, langgraph or langsmith; when copying a snippet from a tutorial or blog; when an import fails (ModuleNotFoundError on langchain.prompts / .chains / .memory); when a call raises TypeError for an unexpected keyword; or when deciding between langchain, langchain-core and langchain-classic.
---

# LangChain API Reference vía MCP — la firma real, no la recordada

`langchain-mcp-docs` dice **qué patrón usar**. Esta skill garantiza que **cada símbolo que se escribe existe, se importa de donde dices y acepta los parámetros que le pasas**. Las dos se usan **siempre juntas** cada vez que se escribe código LangChain.

El 90% de los tutoriales, blogs y respuestas de modelos son **v0**: compilan, no dan warnings y funcionan — por eso el error pasa desapercibido. La referencia de la API es el árbitro.

## Las dos herramientas del MCP `reference-langchain`

### `mcp__reference-langchain__search_api` — encontrar el símbolo y su paquete

```
query: "PostgresSaver"   language: "python"   limit: 5
```
Devuelve el símbolo, su tipo (class/function) y el **paquete** (`langgraph.checkpoint.postgres`). Úsalo cuando no sepas de qué paquete viene algo o busques por palabra clave.

### `mcp__reference-langchain__get_symbol` — firma exacta

```
package: "langchain"   symbol: "create_agent"   language: "python"
```
Devuelve firma completa, tabla de parámetros (requerido / default / tipo), retorno, ejemplo y enlace al código fuente.

- `package` es el nombre de distribución o módulo: `langchain`, `langchain-core`, `langchain-openai`, `langgraph`, `langgraph.checkpoint.postgres`.
- `symbol` puede ser el nombre corto (`ChatOpenAI`) o calificado (`langchain_openai.ChatOpenAI`).
- **Siempre `language: "python"`** en este proyecto.

## Workflow obligatorio

1. Con el patrón ya elegido en `langchain-mcp-docs`, lista **todos** los símbolos LangChain que vas a escribir (funciones, clases, decoradores, middleware, checkpointers).
2. Para cada uno: `search_api` si dudas del paquete → `get_symbol` para la firma.
3. Anota y respeta:
   - **Import exacto** (`from langchain.agents import create_agent`).
   - **Parámetros keyword-only** (todo lo que va tras `*` en la firma — p. ej. `system_prompt=`, `checkpointer=` en `create_agent`).
   - **Nombres reales** de los parámetros (`system_prompt`, no `prompt`).
   - **Tipos aceptados** (`model: str | BaseChatModel`).
4. Si la firma no coincide con el ejemplo de la guía o con el código existente: **la referencia manda** — señálalo al usuario.
5. Tras escribir, **ejecuta los imports** (`python -c "from ... import ..."`) para confirmar contra la versión instalada.

## Tabla v0 → v1: qué esperar al consultar

Atajo para no gastar lookups en lo ya resuelto. **Ante conflicto, gana el MCP** — y hay que actualizar esta tabla.

| Tema | v0 (no escribir) | v1 (idiomático) |
|---|---|---|
| Crear agente | `from langgraph.prebuilt import create_react_agent` | `from langchain.agents import create_agent` |
| Prompt del agente | `prompt=` | `system_prompt=` (str o `SystemMessage`) |
| Prompt dinámico | template con variables / `prompt=` callable | `from langchain.agents.middleware import dynamic_prompt` |
| Memoria | `PostgresChatMessageHistory`, `RunnableWithMessageHistory`, `ConversationBufferMemory` | `checkpointer=` + `thread_id` en el config |
| Checkpointer | — | `langgraph.checkpoint.postgres.PostgresSaver` / `langgraph.checkpoint.memory.InMemorySaver` |
| Bucle de tools | `bind_tools` + `if response.tool_calls:` a mano | `create_agent` lo hace solo |
| Mensajes | `from langchain_core.messages import ...` | `from langchain.messages import ...` (misma clase) |
| Tools | `from langchain_core.tools import tool` | `from langchain.tools import tool` |
| Chains | `LLMChain(llm=, prompt=)` | `prompt \| model \| parser` (LCEL) |
| Agente legacy | `AgentExecutor`, `initialize_agent` | `create_agent` |
| Modelo | `from langchain.chat_models import ChatOpenAI` | `init_chat_model("openai:...")` o `from langchain_openai import ChatOpenAI` |

Test rápido de proyecto v1 — estos imports **fallan** en v1:

```python
import langchain.prompts   # ModuleNotFoundError
import langchain.chains    # ModuleNotFoundError
import langchain.memory    # ModuleNotFoundError
```

### Prompt templates: no son legacy, cambió su ámbito

Viven en `langchain_core.prompts`. Regla:

> `create_agent` → el prompt es un **string** (o `SystemMessage`).
> `prompt | model | parser` → el prompt es un **`ChatPromptTemplate`**.

Para un system prompt estático cargado de YAML, se sustituye con `.replace()` — no se monta un template (así lo hace `agent.py`).

### Checkpointer Postgres

```python
from langgraph.checkpoint.postgres import PostgresSaver

# En este proyecto: PostgresSaver sobre un ConnectionPool (conversation_history/conexion.py),
# no from_conn_string. Una conexión única muere cuando el proveedor la cierra por inactividad
# y psycopg no reconecta; el pool con check=ConnectionPool.check_connection sí.
checkpointer = PostgresSaver(pool)
checkpointer.setup()   # crea las tablas la primera vez
agent = create_agent(model, tools=tools, checkpointer=checkpointer)
```

⚠️ **Supabase:** el pool usa `prepare_threshold=0`, así que funciona tanto en el puerto **5432** (session mode) como en el **6543** (transaction mode). Sin ese parámetro, el 6543 da `DuplicatePreparedStatement`.

## Paquetes: de dónde importar

| Paquete | Qué es | Cuándo |
|---|---|---|
| `langchain` | Lo esencial de agentes (`create_agent`, `init_chat_model`, middleware, tools, messages) | Aplicaciones ← caso normal |
| `langchain-core` | Contratos: `BaseChatModel`, `BaseTool`, `Runnable`/LCEL, prompts | Librerías propias; en apps llega transitivo — **no fijarlo en requirements.txt** |
| `langgraph` | Runtime de grafos, checkpointers, state | Llega vía `langchain` |
| `langchain-openai`, `langchain-postgres`, … | Partner packages | Uno por proveedor |
| `langchain-community` | Integraciones de terceros, calidad desigual | Evitar si existe partner package |
| `langchain-classic` | Lo jubilado: `chains`, `memory`, agentes viejos | Solo para mantener v0 — **nunca por inercia** |

## Checklist antes de dar por bueno código LangChain

1. Cada símbolo pasó por `get_symbol` (o ya estaba verificado en esta sesión).
2. `create_agent`, no `create_react_agent`; `system_prompt=`, no `prompt=`.
3. Si hay `checkpointer`, hay `thread_id` en **cada** invoke.
4. Ningún `if response.tool_calls:` escrito a mano.
5. Ningún import de `langchain.prompts` / `.chains` / `.memory`.
6. `ChatPromptTemplate` solo en cadenas LCEL, nunca como system prompt de agente.
7. Los imports **existen en la versión instalada**: verificado ejecutando, no de memoria.

## Verificación rápida de que el MCP está disponible

```
mcp__reference-langchain__get_symbol  package="langchain"  symbol="create_agent"  language="python"
```
Si la herramienta no existe en la sesión, el MCP `reference-langchain` no está conectado — avisa al usuario antes de continuar (`claude mcp list`).
