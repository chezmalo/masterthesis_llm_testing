import asyncio
import typer
from pathlib import Path
from utils.utils import now_stamp, write_jsonl, load_cases
from src.utils.logger import setup
from src.llm_runner import async_prompt_llm, prompt_llm, ping_llm, parse_answer, build_user_prompt
from llm_schema_prompts.model_prompts import SYSTEM_PROMPT
from src import config

app = typer.Typer(help="LLM Runner für Datentransformationsfluss-Testfälle")

@app.command() 
def run(
    ping: bool = typer.Option(False, help="Ping den LLM-Dienst an und beende das Programm"),
    model: str = typer.Option(config.DEFAULT_MODEL, help="ID des LLM-Modells vom jeweiligen Anbieter ( )"),
    cases: str = typer.Option("src/cases", help="Ordner mit .yaml Testfällen"),
    limit: int = typer.Option(None, help="Limitiere die Anzahl der zu testenden Fälle"),
    out: str = typer.Option("outputs", help="Ausgabeordner"),
    loglevel: str = typer.Option("INFO", help="Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    logfile: bool = typer.Option(True, help="Ob ein Logfile geschrieben werden soll (default: True)"),
    concurrency: int = typer.Option(8, help="Max. gleichzeitige LLM-Requests"),
):
    """
    Starte die Verarbeitung der Testfälle mit dem angegebenen Modell.
    """
    asyncio.run(_run_async(ping, model, cases, limit, out, loglevel, logfile, concurrency))

async def _run_async(
    ping: bool,
    model: str,
    cases: str,
    limit: int | None,
    out: str,
    loglevel: str,
    logfile: bool,
    concurrency: int,
):
    logger = setup(level=loglevel, write_file=logfile)

    # Ping-Check: Wenn --ping gesetzt ist, führe nur einen kurzen Test-Request aus und beende das Programm
    if ping is True:
        logger.info("Führe LLM-Ping durch...")
        ping_llm()
        raise typer.Exit()  

    cases_dir = Path(cases)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starte Verarbeitung der Testfälle...")
    # Fälle laden und nacheinander verarbeiten

    cases_list = []

    try:
        cases_list = load_cases(cases_dir)
        logger.info(f"{len(cases_list)} Fälle aus {cases_dir} geladen.")
    except Exception as e:
        logger.error(f"Fehler beim Laden der Testfälle: {e}")
        raise

    if limit is not None and limit > 0:
        logger.info(f"Limit gesetzt: {limit}. Es werden nur die ersten {limit} Fälle verarbeitet.")
        cases_list = cases_list[:limit]

    logger.info(f"Starte {len(cases_list)} Fälle mit Modell: {model}")

    # Fälle laden und nacheinander verarbeiten
    sem = asyncio.Semaphore(concurrency)

    async def process_case(case, model, out_dir, logger):
        async with sem:
            try:
                logger.debug(f"Verarbeite Fall: {case.get('id', 'unbekannt')}")
                user_prompt = build_user_prompt(case)
                logger.debug(f"User-Prompt erstellt für Fall {case.get('id', 'unbekannt')}.")
                raw = await async_prompt_llm(model, SYSTEM_PROMPT, user_prompt)
                logger.debug(f"Rohantwort vom LLM erhalten für Fall {case.get('id', 'unbekannt')}.")
                parsed = parse_answer(raw)
                logger.debug(f"Antwort geparst und validiert für Fall {case.get('id', 'unbekannt')}.")
    
                # Ergebnis + Quelldatei speichern
                row = parsed.model_dump()
                row["_source_file"] = case["_file"]
    
                # Output-Dateinamen mit Case-Name und Modell generieren
                case_name = Path(case["_file"]).stem
                out_file = out_dir / f"results_{case_name}_{model}_{now_stamp()}.jsonl"
                write_jsonl(out_file, row)
                logger.info(f"[OK] {case['id']} -> gespeichert in {out_file}")
            except Exception as e:
                # Fehler speichern (z.B. Fehler der YAML-Datei, JSON-Parsing-Fehler, Validierungsfehler)
                logger.error(f"Fehler bei Fall {case.get('id')}: {e}")
                out_file = out_dir / f"results_{case.get('id', 'unknown')}_{model}_{now_stamp()}.jsonl"
                write_jsonl(out_file, {"case_id": case.get("id"), "error": str(e)})

    tasks = [
        process_case(case, model, out_dir, logger)
        for case in cases_list
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    app()
