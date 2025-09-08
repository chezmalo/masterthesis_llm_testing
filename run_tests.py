import asyncio
import typer
import time 
import sys
import re
from pathlib import Path
from utils.utils import now_stamp, write_json, load_cases
from src.utils.logger import setup
from src.llm_runner import async_prompt_llm, prompt_llm, ping_llm, parse_answer, build_user_prompt
from src.llm_schema_prompts.model_prompts import SYSTEM_PROMPT
from src import config

app = typer.Typer(help="LLM Runner für Datentransformationsfluss-Testfälle")

# Mapping from short names to full model IDs
MODEL_ALIASES = {
    "gpt": "gpt-5-2025-08-07",
    "claude": "claude-sonnet-4-20250514",
    "google": "gemini-2.5-pro",
}

@app.command() 
def run(
    ping: bool = typer.Option(False, help="Ping den LLM-Dienst an und beende das Programm"),
    model: str = typer.Option(config.DEFAULT_MODEL, help="Komma-separierte Liste von Modell-Kurzbezeichnungen (z.B. gpt,claude,google)"),
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

    # Split and map short names to full model IDs from MODEL_ALIASES
    model_list = []
    for m in model.split(","):
        m = m.strip()
        if not m:
            continue
        model_list.append(MODEL_ALIASES.get(m.lower(), m))
    asyncio.run(_run_async(ping, model_list, cases, limit, out, loglevel, logfile, concurrency))

async def _run_async(
    ping: bool,
    model_list: list[str],
    cases: str,
    limit: int | None,
    out: str,
    loglevel: str,
    logfile: bool,
    concurrency: int,
):
    logger = setup(level=loglevel, write_file=logfile)
    logger.info("LLM Runner gestartet")
    logger.info(f"Verwendete Modelle: {model_list}")
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

    logger.info(f"Starte {len(cases_list)*len(model_list)} Fälle")    

    async def process_case(case, model, out_dir, logger):
        t0 = time.perf_counter()
        logger.info(f"Starte Fall {case.get('id', 'unbekannt')} mit Modell: {model}")
        async with sem:
            try:
                logger.debug(f"Verarbeite Fall: {case.get('id', 'unbekannt')} mit Modell: {model}")
                user_prompt = build_user_prompt(case)
                logger.debug(f"User-Prompt erstellt für Fall {case.get('id', 'unbekannt')}.")
                raw = await async_prompt_llm(model, SYSTEM_PROMPT, user_prompt)
                logger.debug(f"Rohantwort vom LLM erhalten für Fall {case.get('id', 'unbekannt')}.")
                parsed = parse_answer(raw)
                logger.debug(f"Antwort geparst und validiert für Fall {case.get('id', 'unbekannt')}.")
    
                # Ergebnis + Quelldatei speichern
                row = parsed.model_dump()
                row["_source_file"] = case["_file"]
                row["_model"] = model
                row["_duration_seconds"] = round(time.perf_counter() - t0, 3)

                # Output-Dateinamen mit Case-Name und Modell generieren
                case_name = Path(case["_file"]).stem
                # Remove uncessary parts from model name for filename
                model_name = re.sub(r'[-_](\d{4,}([-.]\d{2,})*)$', '', model)
                out_file = out_dir / f"results_{case_name}_{model_name}_{now_stamp()}.json"
                write_json(out_file, row)
                logger.info(f"[OK] {case['id']} -> gespeichert in {out_file} "
                            f"({row['_duration_seconds']}s)")
            except Exception as e:
                # Fehler speichern (z.B. Fehler der YAML-Datei, JSON-Parsing-Fehler, Validierungsfehler)
                duration = round(time.perf_counter() - t0, 3)
                logger.error(f"Fehler bei Fall {case.get('id')}: {e} (nach {duration}s)")
                out_file = out_dir / f"results_{case.get('id', 'unknown')}_{model}_{now_stamp()}.json"
                write_json(out_file, {"case_id": case.get("id"), "error": str(e)})


    # Fälle laden und nacheinander verarbeiten
    sem = asyncio.Semaphore(concurrency)

    # Run all cases for all models
    tasks = [
        process_case(case, model, out_dir, logger)
        for model in model_list
        for case in cases_list
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    app()
