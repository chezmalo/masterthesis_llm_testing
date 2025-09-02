import typer
from pathlib import Path
from utils.utils import now_stamp, write_jsonl, load_cases
from src.utils.logger import setup
from src.llm_runner import prompt_llm, parse_answer, build_user_prompt
from llm_schema_prompts.model_prompts import SYSTEM_PROMPT
from src import config

app = typer.Typer(help="LLM Runner für Data Lineage Testfälle")

@app.command()
def run(
    model: str = typer.Option(config.DEFAULT_MODEL, help="ID des LLM-Modells vom jeweiligen Anbieter ( )"),
    cases: str = typer.Option("src/cases", help="Ordner mit .yaml Testfällen"),
    limit: int = typer.Option(None, help="Limitiere die Anzahl der zu testenden Fälle"),
    out: str = typer.Option("outputs", help="Ausgabeordner"),
    loglevel: str = typer.Option("INFO", help="Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    logfile: bool = typer.Option(True, help="Ob ein Logfile geschrieben werden soll (default: True)"),
):
    """
    Starte die Verarbeitung der Testfälle mit dem angegebenen Modell.
    """
    cases_dir = Path(cases)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger = setup(level=loglevel, write_file=logfile)
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
    
    for case in cases_list:
        try:
            logger.debug(f"Verarbeite Fall: {case.get('id', 'unbekannt')}")
            user_prompt = build_user_prompt(case)
            logger.debug(f"User-Prompt erstellt für Fall {case.get('id', 'unbekannt')}.")
            raw = prompt_llm(model, SYSTEM_PROMPT, user_prompt)
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

if __name__ == "__main__":
    app()
