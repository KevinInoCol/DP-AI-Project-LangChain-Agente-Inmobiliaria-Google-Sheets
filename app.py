"""
Interfaz Streamlit para el Agente IA de Google Sheets.

Uso:
    streamlit run app.py
"""

from datetime import datetime
import streamlit as st
from sheets_reader import load_sheet_as_dataframe, get_sheet_summary
from agent import build_agent, ask

# ── Configuración de la página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Agente IA — Google Sheets",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos personalizados ────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stChatMessage"] { border-radius: 12px; margin-bottom: 8px; }
    .stButton > button { border-radius: 8px; }
    .metric-label { font-size: 12px; color: #888; }
    [data-testid="stSidebar"] { background-color: #0f1117; }
</style>
""", unsafe_allow_html=True)

EXAMPLE_QUESTIONS = [
    "¿Cuál es el precio promedio por distrito?",
    "¿Cuántos departamentos tienen piscina?",
    "¿Cuál es el costo total promedio (alquiler + condominio)?",
    "¿Cuál es el distrito más barato para alquilar?",
    "Muéstrame los 5 departamentos más grandes",
]

# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],
        "df": None,
        "agent": None,
        "sheet_name": None,
        "loaded_at": None,
        "pending_question": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# ── Carga de datos ────────────────────────────────────────────────────────────
def load_data():
    """Carga Google Sheets y construye el agente. Guarda en session_state."""
    df, spreadsheet_title, sheet_title = load_sheet_as_dataframe()
    display_name = f"{spreadsheet_title} → {sheet_title}"

    st.session_state.df = df
    st.session_state.agent = build_agent(df, display_name)
    st.session_state.sheet_name = display_name
    st.session_state.loaded_at = datetime.now().strftime("%H:%M:%S")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Agente IA")
    st.caption("Consulta Google Sheets en lenguaje natural")
    st.divider()

    # Estado de conexión
    if st.session_state.df is not None:
        df = st.session_state.df

        st.success(f"**{st.session_state.sheet_name}**", icon="✅")
        st.caption(f"Datos cargados a las {st.session_state.loaded_at}")

        col1, col2 = st.columns(2)
        col1.metric("Filas", f"{len(df):,}")
        col2.metric("Columnas", len(df.columns))

        with st.expander("📋 Columnas disponibles"):
            for col in df.columns:
                st.markdown(f"- `{col}`")

        with st.expander("🔍 Vista previa (5 filas)"):
            st.dataframe(df.head(5), width="stretch")

        with st.expander("📊 Estadísticas numéricas"):
            st.dataframe(
                df.describe().round(2),
                width="stretch",
            )
    else:
        st.info("Conectando a Google Sheets...")

    st.divider()

    # Ejemplos de preguntas
    st.subheader("💡 Preguntas de ejemplo")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True, key=f"btn_{q[:20]}"):
            st.session_state.pending_question = q

    st.divider()

    # Botón de recarga
    if st.button("🔄 Recargar datos", use_container_width=True, type="secondary"):
        st.session_state.df = None
        st.session_state.agent = None
        st.session_state.loaded_at = None
        st.rerun()

    # Botón para limpiar el chat
    if st.button("🗑️ Limpiar conversación", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

# ── Área principal ────────────────────────────────────────────────────────────
st.title("🤖 Agente IA — Google Sheets")
st.caption("Haz preguntas en lenguaje natural sobre tus datos")

# Carga inicial si no hay datos
if st.session_state.df is None:
    with st.spinner("Conectando a Google Sheets e inicializando agente..."):
        try:
            load_data()
            st.rerun()
        except FileNotFoundError as e:
            st.error(f"**Error de credenciales:** {e}")
            st.info(
                "Asegúrate de que `credentials.json` (o el archivo configurado en "
                "`GOOGLE_CREDENTIALS_PATH`) exista en el directorio del proyecto."
            )
            st.stop()
        except Exception as e:
            st.error(f"**Error al cargar la hoja:** {type(e).__name__}: {e or '(sin mensaje)'}")
            st.info(
                "Verifica que `SPREADSHEET_ID` y `SHEET_NAME` en tu `.env` sean correctos "
                "y que el Sheet esté compartido con la cuenta de servicio."
            )
            st.stop()

# Historial del chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "timestamp" in message:
            st.caption(f"datos de {message['timestamp']}")

# Procesar pregunta de botón del sidebar
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        with st.spinner("Actualizando datos y analizando..."):
            try:
                load_data()
                response = ask(st.session_state.agent, question)
            except Exception as e:
                response = f"Error al procesar la pregunta: {e}"
        st.markdown(response)
        st.caption(f"datos de {st.session_state.loaded_at}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "timestamp": st.session_state.loaded_at,
    })
    st.rerun()

# Input de chat
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Actualizando datos y analizando..."):
            try:
                load_data()
                response = ask(st.session_state.agent, prompt)
            except Exception as e:
                response = f"Error al procesar la pregunta: {e}"
        st.markdown(response)
        st.caption(f"datos de {st.session_state.loaded_at}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "timestamp": st.session_state.loaded_at,
    })
