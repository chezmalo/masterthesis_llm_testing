import typer
import asyncio
from src import config
from src.runner.runner import _run_async
from src.utils.utils import get_model_list
from src.llm_schema_prompts.model_prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_ROBUST, USER_PROMPT_TEMPLATE, USER_PROMPT_TEMPLATE_ROBUST


app = typer.Typer(help="LLM Runner für Datentransformationsfluss-Testfälle")

@app.command() 
def run(
    ping: bool = typer.Option(False, help="Ping den LLM-Dienst an und beende das Programm"),
    model: str = typer.Option(config.DEFAULT_MODEL, help="Komma-separierte Liste von Modell-Kurzbezeichnungen (z.B. gpt,claude,google)"),
    input: str = typer.Option("inputs", help="Ordner mit .yaml Testfällen"),
    limit: int = typer.Option(None, help="Limitiere die Anzahl der zu testenden Fälle"),
    output: str = typer.Option("outputs", help="Ausgabeordner"),
    loglevel: str = typer.Option("INFO", help="Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    logfile: bool = typer.Option(True, help="Soll ein Logfile geschrieben werden? (default: True)"),
    concurrency: int = typer.Option(8, help="Max. gleichzeitige LLM-Requests"),
    repeat: int = typer.Option(1, help="Wie oft soll jeder Fall ausgeführt werden? (Testen der Konsistenz) (default: 1)"),
    stream: bool = typer.Option(False, help="Nutze Streaming für LLM-Antworten (default: False)"),  
):
    """
    Starte die Verarbeitung der Testfälle mit dem angegebenen Modell.
    """ 

    # Split and map short names to full model IDs from MODEL_ALIASES
    model_list = get_model_list(model)

    # Define prompt configs: two initial, one robust
    prompt_configs = [
        {"system_prompt": SYSTEM_PROMPT, "user_prompt_builder": USER_PROMPT_TEMPLATE},
        {"system_prompt": SYSTEM_PROMPT, "user_prompt_builder": USER_PROMPT_TEMPLATE},
        {"system_prompt": SYSTEM_PROMPT_ROBUST, "user_prompt_builder": USER_PROMPT_TEMPLATE_ROBUST},
    ]
    asyncio.run(_run_async(
        ping, model_list, input, limit, output, loglevel, logfile, concurrency, repeat, prompt_configs, stream  
    ))

if __name__ == "__main__":
    app()