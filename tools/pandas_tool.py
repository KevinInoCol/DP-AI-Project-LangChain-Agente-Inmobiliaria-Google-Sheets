"""
Tool para ejecutar código Python sobre un DataFrame de pandas.

El DataFrame se inyecta mediante un closure en build_pandas_tool(),
lo que permite que la tool sea stateless pero tenga acceso a los datos
sin necesidad de variables globales.
"""

import io
import contextlib
import traceback
import pandas as pd
from langchain_core.tools import tool


def build_pandas_tool(df: pd.DataFrame):
    """
    Fábrica que retorna una tool de LangChain con el DataFrame capturado.

    Args:
        df: DataFrame sobre el que operará la tool

    Returns:
        Tool decorada con @tool lista para pasarse al agente
    """

    @tool
    def execute_python(code: str) -> str:
        """
        Ejecuta código Python sobre el DataFrame `df` para analizar los datos.
        Usa print() para mostrar resultados. El DataFrame ya está cargado como `df`.
        Ejemplo: print(df.groupby('producto')['ventas'].sum())
        """
        output = io.StringIO()
        local_vars = {"df": df, "pd": pd}
        try:
            with contextlib.redirect_stdout(output):
                exec(code, local_vars)  # noqa: S102
            result = output.getvalue()
            return (
                result
                if result.strip()
                else "Código ejecutado sin salida. Usa print() para ver resultados."
            )
        except Exception:
            tb = traceback.format_exc()
            available_cols = df.columns.tolist()
            return (
                f"Error al ejecutar el código:\n{tb}\n"
                f"Columnas disponibles en df: {available_cols}\n"
                "Corrige el código y vuelve a intentarlo."
            )

    return execute_python
