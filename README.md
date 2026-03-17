# 🤖 Agente IA — Consulta Google Sheets

Agente de IA construido con **LangChain v1** que permite hacer preguntas en lenguaje natural sobre los datos de tu Google Sheets. Disponible con interfaz web (Streamlit) o desde la terminal (CLI).

## Características

- Consultas en lenguaje natural en **español**
- Conexión directa a **Google Sheets** vía API (cuenta de servicio)
- Análisis de datos con **pandas** — los datos se recargan automáticamente en cada consulta
- **Interfaz web** con Streamlit (chat, sidebar con estadísticas, preguntas de ejemplo)
- **Interfaz CLI** con colores y formato para uso en terminal
- Prompt con personalidad de consultor inmobiliario especializado en São Paulo

---

## Estructura del proyecto

```
.
├── app.py               # Interfaz web Streamlit (recomendada)
├── main.py              # Interfaz CLI (terminal)
├── agent.py             # Agente LangChain v1 (init_chat_model + create_agent)
├── sheets_reader.py     # Conexión y lectura de Google Sheets
├── tools/
│   ├── __init__.py
│   └── pandas_tool.py   # Tool @execute_python para análisis de datos
├── requirements.txt
├── .env                 # Variables de entorno (NO subir a git)
├── .env.example         # Plantilla
└── credentials.json     # Credenciales Google (NO subir a git)
```

---

## Configuración (paso a paso)

### 1. Crear credenciales de Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto o usa uno existente
3. En el menú lateral, ve a **APIs y servicios → Biblioteca**
4. Busca y habilita **Google Sheets API** y **Google Drive API**
5. Ve a **APIs y servicios → Credenciales**
6. Haz clic en **Crear credenciales → Cuenta de servicio**
7. Dale un nombre y haz clic en **Crear**
8. En la lista de cuentas de servicio, entra a la que creaste
9. Ve a **Claves → Agregar clave → Crear clave nueva → JSON**
10. Descarga el JSON y colócalo en la raíz del proyecto

### 2. Compartir el Google Sheet con la cuenta de servicio

1. Abre el JSON descargado y copia el valor de `"client_email"`
   (algo como `nombre@proyecto.iam.gserviceaccount.com`)
2. Abre tu Google Sheet → **Compartir** → pega ese email → rol **Lector**

### 3. Obtener el ID del spreadsheet

```
https://docs.google.com/spreadsheets/d/AQUI_ESTA_EL_ID/edit
```

### 4. Configurar el archivo `.env`

```bash
cp .env.example .env
```

Rellena los valores en `.env`:

```env
OPENAI_API_KEY=sk-...
SPREADSHEET_ID=el-id-de-tu-hoja
SHEET_NAME=Hoja 1
GOOGLE_CREDENTIALS_PATH=credentials.json
OPENAI_MODEL=gpt-4o-mini
```

### 5. Crear entorno conda e instalar dependencias

```bash
conda create -n agente-sheets python=3.11 -y
conda activate agente-sheets
pip install -r requirements.txt
```

---

## Uso

### Interfaz web (Streamlit) — recomendada

```bash
conda activate agente-sheets
streamlit run app.py
```

Se abre automáticamente en `http://localhost:8501`

### Interfaz CLI (terminal)

```bash
conda activate agente-sheets
python main.py
```

### Opciones del CLI

```bash
# Usar una hoja específica
python main.py --sheet "Ventas 2024"

# Usar un spreadsheet diferente
python main.py --spreadsheet-id "otro-id-aqui"

# Usar GPT-4o (más potente)
python main.py --model openai:gpt-4o
```

---

## Comandos dentro del CLI

| Comando | Descripción |
|---------|-------------|
| `/ayuda` | Muestra el menú de ayuda |
| `/resumen` | Estadísticas generales de la hoja |
| `/columnas` | Lista todas las columnas disponibles |
| `/muestra` | Muestra las primeras 5 filas |
| `/salir` | Termina el programa |

---

## Ejemplos de preguntas

```
¿Cuál es el departamento más caro?
¿Cuál es el precio promedio de alquiler por distrito?
¿Cuántos departamentos tienen piscina?
¿Cuál es el costo total promedio (alquiler + condominio)?
¿Cuál es el distrito más barato para alquilar?
Muéstrame los 5 departamentos más grandes
¿Cuántos departamentos tienen ascensor y están amueblados?
```

---

## Cómo funciona el agente

```
Pregunta del usuario
       ↓
Recarga datos frescos desde Google Sheets (cada consulta)
       ↓
LLM genera código Python basado en el esquema del DataFrame
       ↓
Tool execute_python ejecuta el código localmente sobre el DataFrame
       ↓
LLM verbaliza el resultado en español
```

El LLM **nunca ve las filas completas** — solo el esquema, una muestra de 3 filas, y el resultado del código ejecutado. Esto hace que el consumo de tokens sea bajo independientemente del tamaño del dataset.

---

> ⚠️ **Importante:** Nunca subas `credentials.json` ni `.env` a Git. Ambos están en `.gitignore`.
