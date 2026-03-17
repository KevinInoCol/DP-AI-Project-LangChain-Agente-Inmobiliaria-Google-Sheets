"""
CLI interactivo para consultar Google Sheets con un Agente de IA.

Uso:
    python main.py
    python main.py --sheet "Ventas 2024"
    python main.py --model openai:gpt-4o
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Callable
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from rich import box

from sheets_reader import load_sheet_as_dataframe, get_sheet_summary
from agent import build_agent, ask

load_dotenv()

console = Console()

BANNER = """
[bold cyan]╔══════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]  [bold white]🤖 Agente IA — Consulta Google Sheets[/bold white]      [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]  [dim]Haz preguntas en lenguaje natural sobre[/dim]    [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]  [dim]tus datos directamente desde la terminal[/dim]   [bold cyan]║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════╝[/bold cyan]
"""

HELP_COMMANDS = {
    "/ayuda": "Muestra este menú de ayuda",
    "/resumen": "Muestra un resumen de la hoja activa",
    "/columnas": "Lista las columnas disponibles",
    "/muestra": "Muestra las primeras 5 filas de datos",
    "/salir": "Termina el programa",
}

EXAMPLE_QUESTIONS = [
    "¿Cuáles son las ventas totales?",
    "¿Cuál es el producto más vendido?",
    "¿Cuántas filas hay en total?",
    "Muéstrame un resumen por mes",
    "¿Cuál es el promedio de ventas por región?",
]


def print_banner():
    console.print(BANNER)


def print_help():
    table = Table(title="Comandos disponibles", box=box.ROUNDED, border_style="cyan")
    table.add_column("Comando", style="bold yellow")
    table.add_column("Descripción", style="white")
    for cmd, desc in HELP_COMMANDS.items():
        table.add_row(cmd, desc)
    console.print(table)

    console.print("\n[bold]Ejemplos de preguntas:[/bold]")
    for q in EXAMPLE_QUESTIONS:
        console.print(f"  [dim]→[/dim] [italic]{q}[/italic]")
    console.print()


def print_dataframe_preview(df):
    table = Table(
        title=f"Primeras {min(5, len(df))} filas",
        box=box.SIMPLE_HEAVY,
        border_style="dim",
        show_lines=True,
    )
    for col in df.columns:
        table.add_column(str(col), style="cyan", overflow="fold")
    for _, row in df.head(5).iterrows():
        table.add_row(*[str(v) for v in row])
    console.print(table)


def run_interactive_session(
    sheet_name: str,
    reload_fn: Callable[[], tuple],
):
    """
    Ejecuta la sesión interactiva de preguntas y respuestas.

    Antes de cada pregunta recarga los datos frescos desde Google Sheets
    para garantizar que el agente siempre trabaja con información actualizada.

    Args:
        sheet_name: Nombre de la hoja para mostrar en la UI
        reload_fn: Función que retorna (df, agent) con datos frescos de Google Sheets
    """
    df, agent = reload_fn()

    console.print(
        Panel(
            f"[bold green]✓ Datos cargados:[/bold green] [white]{sheet_name}[/white]  "
            f"[dim]({len(df):,} filas × {len(df.columns)} columnas)[/dim]\n"
            f"[dim]Los datos se actualizan automáticamente en cada consulta.[/dim]\n"
            f"[dim]Escribe [bold]/ayuda[/bold] para ver los comandos disponibles "
            f"o [bold]/salir[/bold] para terminar.[/dim]",
            border_style="green",
        )
    )
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]Tú[/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Hasta luego 👋[/dim]")
            break

        if not user_input:
            continue

        # --- Comandos especiales ---
        if user_input.lower() in ("/salir", "/exit", "/quit", "exit", "quit"):
            console.print("[dim]Hasta luego 👋[/dim]")
            break

        elif user_input.lower() in ("/ayuda", "/help"):
            print_help()

        elif user_input.lower() == "/resumen":
            summary = get_sheet_summary(df, sheet_name)
            console.print(
                Panel(summary, title="Resumen de la hoja", border_style="blue")
            )

        elif user_input.lower() == "/columnas":
            cols = "\n".join(
                f"  [bold cyan]{i+1}.[/bold cyan] {col}" for i, col in enumerate(df.columns)
            )
            console.print(
                Panel(cols, title=f"Columnas ({len(df.columns)})", border_style="blue")
            )

        elif user_input.lower() == "/muestra":
            print_dataframe_preview(df)

        # --- Pregunta al agente ---
        else:
            with console.status(
                "[bold yellow]Actualizando datos...[/bold yellow]", spinner="dots"
            ):
                df, agent = reload_fn()

            loaded_at = datetime.now().strftime("%H:%M:%S")

            with console.status(
                "[bold yellow]Analizando...[/bold yellow]", spinner="dots"
            ):
                response = ask(agent, user_input)

            console.print()
            console.print(
                Panel(
                    Markdown(response),
                    title=f"[bold green]Agente IA[/bold green]  [dim](datos de {loaded_at})[/dim]",
                    border_style="green",
                    padding=(1, 2),
                )
            )
            console.print()

    return "exit"


def main():
    parser = argparse.ArgumentParser(
        description="Agente IA para consultar Google Sheets en lenguaje natural."
    )
    parser.add_argument(
        "--sheet",
        type=str,
        help="Nombre de la hoja a consultar (sobreescribe SHEET_NAME del .env)",
    )
    parser.add_argument(
        "--spreadsheet-id",
        type=str,
        help="ID del spreadsheet (sobreescribe SPREADSHEET_ID del .env)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Modelo a usar en formato proveedor:modelo (ej: openai:gpt-4o-mini, openai:gpt-4o)",
    )
    args = parser.parse_args()

    print_banner()

    # Carga inicial para obtener el nombre del spreadsheet
    console.print("[yellow]Conectando a Google Sheets...[/yellow]")
    try:
        df_init, spreadsheet_title, sheet_title = load_sheet_as_dataframe(
            spreadsheet_id=args.spreadsheet_id,
            sheet_name=args.sheet,
        )
    except FileNotFoundError as e:
        console.print(f"\n[bold red]Error de credenciales:[/bold red] {e}")
        console.print(
            "[dim]Consulta el archivo [bold]README.md[/bold] para saber cómo "
            "configurar las credenciales de Google.[/dim]"
        )
        sys.exit(1)
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e) or "(sin mensaje)"
        console.print(f"\n[bold red]Error ({error_type}):[/bold red] {error_msg}")

        if "SpreadsheetNotFound" in error_type or "404" in error_msg:
            console.print(
                "[dim]→ El spreadsheet no existe o no fue compartido con la cuenta de servicio.\n"
                f"  Verifica que [bold]SPREADSHEET_ID={os.getenv('SPREADSHEET_ID')}[/bold] sea correcto\n"
                "  y que hayas compartido la hoja con el email de la cuenta de servicio.[/dim]"
            )
        elif "WorksheetNotFound" in error_type or "worksheet" in error_msg.lower():
            console.print(
                f"[dim]→ La hoja [bold]{os.getenv('SHEET_NAME')}[/bold] no existe en el spreadsheet.\n"
                "  Verifica el valor de [bold]SHEET_NAME[/bold] en tu archivo .env.\n"
                "  Asegúrate de que el nombre coincide exactamente (mayúsculas/minúsculas).[/dim]"
            )
        elif "PERMISSION_DENIED" in error_msg or "403" in error_msg:
            console.print(
                "[dim]→ Sin permisos de acceso. Comparte el Google Sheet con el email\n"
                "  de tu cuenta de servicio (lo encuentras en credentials.json como 'client_email').[/dim]"
            )
        else:
            console.print(
                "[dim]→ Verifica que [bold]SPREADSHEET_ID[/bold], [bold]SHEET_NAME[/bold] y\n"
                "  [bold]GOOGLE_CREDENTIALS_PATH[/bold] estén correctos en tu archivo .env.[/dim]"
            )
        sys.exit(1)

    display_name = f"{spreadsheet_title} → {sheet_title}"

    console.print(
        f"[yellow]Inicializando agente con modelo "
        f"[bold]{args.model or 'openai:gpt-4o-mini'}[/bold]...[/yellow]"
    )

    def reload_fn() -> tuple:
        """Carga datos frescos de Google Sheets y construye un agente nuevo."""
        df, _, _ = load_sheet_as_dataframe(
            spreadsheet_id=args.spreadsheet_id,
            sheet_name=args.sheet,
        )
        agent = build_agent(df=df, sheet_name=display_name, model=args.model)
        return df, agent

    try:
        run_interactive_session(
            sheet_name=display_name,
            reload_fn=reload_fn,
        )
    except Exception as e:
        console.print(f"\n[bold red]Error al iniciar el agente:[/bold red] {e}")
        console.print(
            "\n[dim]Verifica que tu [bold]OPENAI_API_KEY[/bold] esté configurada "
            "correctamente en el archivo [bold].env[/bold].[/dim]"
        )


if __name__ == "__main__":
    main()
