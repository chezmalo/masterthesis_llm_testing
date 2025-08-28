import argparse
from pathlib import Path
from src.utils import now_stamp, write_jsonl, load_cases
from src.llm_runner import ask_llm, parse_answer, build_user_prompt, SYSTEM_PROMPT
from src import config

def main():
    # CLI Argumente parsen (Modell, Cases-Ordner, Output-Datei)
    parser = argparse.ArgumentParser(description="LLM Runner für Data Lineage Testfälle")
    parser.add_argument("--model", default=config.DEFAULT_MODEL, help="ID des LLM-Modells vom jeweiligen Anbieter (LLM-Stats)")
    parser.add_argument("--cases", default="src/cases", help="Ordner mit .yaml Testfällen")
    parser.add_argument("--limit", default=None, help="Limitierte die Anzahl der zu testenden Fälle", type=int)
    parser.add_argument("--out", default="outputs", help="Ausgabeordner")
    args = parser.parse_args()

    cases_dir = Path(args.cases)
    out_file = Path(args.out) / f"results_{args.model.replace('/','_')}_{now_stamp()}.jsonl"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    limit = args.limit 
    # Fälle laden und nacheinander verarbeiten
    cases = load_cases(cases_dir)
    if limit is not None and limit > 0:
        cases = cases[:limit]
    print(f"Starte {len(cases)} Fälle mit Modell: {args.model}")
    for case in cases:
        try:
            # User-Prompt bauen, LLM die Prompts übergeben, Antwort parsen
            user_prompt = build_user_prompt(case)
            raw = ask_llm(args.model, SYSTEM_PROMPT, user_prompt)
            parsed = parse_answer(raw)
            # Ergebnis + Quelldatei speichern
            row = parsed.model_dump()
            row["_source_file"] = case["_file"]
            write_jsonl(out_file, row)
            print(f"[OK] {case['id']} -> gespeichert")
        except Exception as e:
            # Fehler speichern (z.B. Fehler der YAML-Datei, JSON-Parsing-Fehler, Validierungsfehler)
            write_jsonl(out_file, {"case_id": case.get("id"), "error": str(e)})
            print(f"[FEHLER] {case.get('id')}: {e}")

if __name__ == "__main__":
    main()
