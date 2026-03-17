"""
Módulo para leer datos de Google Sheets y convertirlos en DataFrames de pandas.
"""

import os
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_google_client() -> gspread.Client:
    """Autentica y retorna un cliente de Google Sheets."""
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"No se encontró el archivo de credenciales: '{credentials_path}'\n"
            "Por favor, descarga el archivo JSON de tu cuenta de servicio de Google Cloud "
            "y colócalo en este directorio."
        )

    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    return gspread.authorize(creds)


def load_sheet_as_dataframe(
    spreadsheet_id: str | None = None,
    sheet_name: str | None = None,
) -> tuple[pd.DataFrame, str, str]:
    """
    Carga una hoja de Google Sheets como DataFrame de pandas.

    Returns:
        Tuple de (DataFrame, spreadsheet_title, sheet_title)
    """
    spreadsheet_id = spreadsheet_id or os.getenv("SPREADSHEET_ID")
    sheet_name = sheet_name or os.getenv("SHEET_NAME", "Sheet1")

    if not spreadsheet_id:
        raise ValueError(
            "No se especificó SPREADSHEET_ID. "
            "Agrégalo en tu archivo .env o pásalo como parámetro."
        )

    client = get_google_client()
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.worksheet(sheet_name)

    data = worksheet.get_all_records()

    if not data:
        raise ValueError(
            f"La hoja '{sheet_name}' está vacía o no tiene encabezados válidos."
        )

    df = pd.DataFrame(data)

    # Eliminar columnas sin nombre (artefacto de columnas índice en Google Sheets)
    df = df.loc[:, df.columns != ""]
    df.columns = [str(c).strip() for c in df.columns]

    # Inferir tipos de datos automáticamente
    df = _infer_dtypes(df)

    return df, spreadsheet.title, worksheet.title


def load_all_sheets(spreadsheet_id: str | None = None) -> dict[str, pd.DataFrame]:
    """Carga todas las hojas de un spreadsheet como DataFrames."""
    spreadsheet_id = spreadsheet_id or os.getenv("SPREADSHEET_ID")

    if not spreadsheet_id:
        raise ValueError("No se especificó SPREADSHEET_ID.")

    client = get_google_client()
    spreadsheet = client.open_by_key(spreadsheet_id)

    sheets = {}
    for worksheet in spreadsheet.worksheets():
        data = worksheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            sheets[worksheet.title] = _infer_dtypes(df)

    return sheets


def _infer_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Intenta convertir columnas de texto a tipos numéricos o de fecha cuando es posible."""
    import warnings

    for col in df.columns:
        # Intentar convertir a numérico
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().sum() > len(df) * 0.7:
            df[col] = numeric
            continue

        # Intentar convertir a fecha (suprimir warning de formato)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                date_col = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            if date_col.notna().sum() > len(df) * 0.7:
                df[col] = date_col
        except Exception:
            pass

    return df


def get_sheet_summary(df: pd.DataFrame, sheet_name: str) -> str:
    """Genera un resumen textual del contenido de la hoja."""
    lines = [
        f"Hoja: {sheet_name}",
        f"Filas: {len(df):,} | Columnas: {len(df.columns)}",
        f"Columnas: {', '.join(df.columns.tolist())}",
        "",
        "Tipos de datos:",
    ]
    for col, dtype in df.dtypes.items():
        lines.append(f"  - {col}: {dtype}")

    if df.select_dtypes(include="number").columns.any():
        lines.append("\nEstadísticas numéricas:")
        lines.append(df.describe().to_string())

    return "\n".join(lines)
