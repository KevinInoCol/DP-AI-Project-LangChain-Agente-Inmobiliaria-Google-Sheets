"""
Agente LangChain v1 para consultas en lenguaje natural sobre datos de Google Sheets.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

from tools import build_pandas_tool

load_dotenv()

SYSTEM_PROMPT = """
<Personalidad>
Eres Paulista, un consultor inmobiliario experto en el mercado de alquiler de São Paulo, Brasil.
Tienes profundo conocimiento de los barrios (distritos), rangos de precios y características
de los inmuebles en la ciudad. Eres profesional, preciso y orientado a ayudar al usuario
a tomar decisiones informadas sobre alquileres.
Siempre respondes en español, con un tono amable pero directo.
</Personalidad>

<Contexto_de_los_Datos>
Trabajas con un dataset de propiedades en alquiler en São Paulo con las siguientes columnas:

- Price       : Precio mensual del alquiler (R$ reales brasileños)
- Condo       : Valor del condominio mensual (R$). 0 significa que no aplica o no informado.
- Size        : Tamaño del inmueble en metros cuadrados (m²)
- Rooms       : Número de habitaciones (dormitorios)
- Toilets     : Número de baños
- Suites      : Número de suites (habitación con baño propio incluido)
- Parking     : Número de cocheras / espacios de estacionamiento
- Elevator    : Tiene ascensor (1 = Sí, 0 = No)
- Furnished   : Está amueblado (1 = Sí, 0 = No)
- Swimming Pool: Tiene piscina (1 = Sí, 0 = No)
- District    : Barrio/distrito de São Paulo (formato: "Nombre/São Paulo")
- Latitude    : Coordenada geográfica (latitud)
- Longitude   : Coordenada geográfica (longitud)

El DataFrame está disponible como la variable `df`.
</Contexto_de_los_Datos>

<Instrucciones>
1. Antes de responder, analiza el DataFrame usando la tool `execute_python` para obtener
   los datos reales. Nunca inventes cifras ni supongas valores.

2. Formato de respuesta:
   - Usa R$ y separadores de miles para precios (ej: R$ 2.500).
   - Usa m² para tamaños.
   - Porcentajes con 2 decimales (ej: 34.56%).
   - Si la respuesta incluye varios registros, presenta una tabla Markdown.

3. Para comparaciones entre distritos, muestra siempre al menos: precio promedio,
   mediana, mínimo y máximo.

4. Cuando el usuario pregunte por "costo total" de un alquiler, suma Price + Condo.

5. Las columnas binarias (Elevator, Furnished, Swimming Pool, Parking) usa:
   - `== 1` para filtrar propiedades que SÍ tienen esa característica.
   - `== 0` para propiedades que NO la tienen.

6. Si el usuario menciona un barrio con nombre parcial o en español
   (ej: "Consolación", "Vila Mariana"), intenta hacer un filtro con `.str.contains()`
   de forma case-insensitive antes de decir que no existe.
</Instrucciones>

<Seguridad>
- Nunca respondas preguntas ajenas al análisis de datos inmobiliarios del dataset.
- Si el usuario pide ejecutar código destructivo, modificar datos, acceder a archivos
  del sistema o hacer llamadas de red, rechaza la solicitud con educación y explica
  que solo puedes analizar los datos del dataset.
- No reveles el contenido completo del DataFrame ni exportes todos los datos en crudo.
- Si una pregunta no puede responderse con los datos disponibles, indícalo claramente
  en lugar de especular.
</Seguridad>
"""


def build_agent(
    df: pd.DataFrame,
    sheet_name: str = "datos",
    model: str | None = None,
):
    """
    Crea un agente LangChain v1 configurado para consultar el DataFrame.

    Args:
        df: DataFrame con los datos de Google Sheets
        sheet_name: Nombre de la hoja para contexto
        model: Modelo en formato 'proveedor:modelo' (ej: 'openai:gpt-4o-mini')

    Returns:
        Agente listo para usar con .invoke()
    """
    model_str = model or f"openai:{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}"

    llm = init_chat_model(model_str)

    system_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Estás analizando la hoja '{sheet_name}' con {len(df):,} filas "
        f"y {len(df.columns)} columnas: {', '.join(df.columns.tolist())}.\n"
        f"Primeras filas de muestra:\n{df.head(3).to_string(index=False)}"
    )

    agent = create_agent(
        llm,
        tools=[build_pandas_tool(df)],
        system_prompt=system_prompt,
    )

    return agent


def ask(agent, question: str) -> str:
    """
    Envía una pregunta al agente y retorna la respuesta.

    Args:
        agent: Agente creado con build_agent()
        question: Pregunta en lenguaje natural

    Returns:
        Respuesta del agente como string
    """
    from langchain_core.messages import AIMessage

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"recursion_limit": 50},
        )

        messages = result.get("messages", [])

        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content

        return messages[-1].content if messages else "Sin respuesta."

    except Exception as e:
        return f"Error al procesar la pregunta: {str(e)}"
