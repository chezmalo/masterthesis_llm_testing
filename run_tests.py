import argparse
from pathlib import Path
from utils.utils import now_stamp, write_jsonl, load_cases
from src.utils.logger import setup_logger
from src.llm_runner import prompt_llm, parse_answer, build_user_prompt
from llm_schema_prompts.model_prompts import SYSTEM_PROMPT
from src import config

def main():
    # CLI Argumente parsen (Modell, Cases-Ordner, Output-Datei, Logging)
    parser = argparse.ArgumentParser(description="LLM Runner für Data Lineage Testfälle")
    parser.add_argument("--model", default=config.DEFAULT_MODEL, help="ID des LLM-Modells vom jeweiligen Anbieter (LLM-Stats)")
    parser.add_argument("--cases", default="src/cases", help="Ordner mit .yaml Testfällen")
    parser.add_argument("--limit", default=None, help="Limitierte die Anzahl der zu testenden Fälle", type=int)
    parser.add_argument("--out", default="outputs", help="Ausgabeordner")
    parser.add_argument("--loglevel", default="INFO", help="Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    args = parser.parse_args()

    cases_dir = Path(args.cases)
    out_file = Path(args.out) / f"results_{args.model.replace('/','_')}_{now_stamp()}.jsonl"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    limit = args.limit 

    logger = setup_logger(level=args.loglevel, write_file=True)
    logger.info("Starte Verarbeitung der Testfälle...")
    # Fälle laden und nacheinander verarbeiten
    try:
        cases = load_cases(cases_dir)
        logger.info(f"{len(cases)} Fälle aus {cases_dir} geladen.")
    except Exception as e:
        logger.error(f"Fehler beim Laden der Testfälle: {e}")
        raise

    if limit is not None and limit > 0:
        logger.info(f"Limit gesetzt: {limit}. Es werden nur die ersten {limit} Fälle verarbeitet.")
        cases = cases[:limit]
    logger.info(f"Starte {len(cases)} Fälle mit Modell: {args.model}")
    for case in cases:
        try:
            logger.debug(f"Verarbeite Fall: {case.get('id', 'unbekannt')}")
            # User-Prompt bauen, LLM die Prompts übergeben, Antwort parsen
            user_prompt = build_user_prompt(case)
            logger.debug(f"User-Prompt erstellt für Fall {case.get('id', 'unbekannt')}.")
            raw = prompt_llm(args.model, SYSTEM_PROMPT, user_prompt)
            logger.debug(f"Rohantwort vom LLM erhalten für Fall {case.get('id', 'unbekannt')}.")
            parsed = parse_answer(raw)
            logger.debug(f"Antwort geparst und validiert für Fall {case.get('id', 'unbekannt')}.")

            # Ergebnis + Quelldatei speichern
            row = parsed.model_dump()
            row["_source_file"] = case["_file"]

            # Output-Dateinamen mit Case-Name und Modell generieren
            case_name = Path(case["_file"]).stem
            out_file = Path(args.out) / f"results_{case_name}_{args.model}_{now_stamp()}.jsonl"
            write_jsonl(out_file, row)
            logger.info(f"[OK] {case['id']} -> gespeichert in {out_file}")
        except Exception as e:
            # Fehler speichern (z.B. Fehler der YAML-Datei, JSON-Parsing-Fehler, Validierungsfehler)
            logger.error(f"Fehler bei Fall {case.get('id')}: {e}")
            write_jsonl(out_file, {"case_id": case.get("id"), "error": str(e)})

if __name__ == "__main__":
    main()
