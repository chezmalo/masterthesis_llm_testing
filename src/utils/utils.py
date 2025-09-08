import logging
from pathlib import Path
from datetime import datetime
import json
import time
import yaml
import re

logger = logging.getLogger(__name__)

# gives current timestamp in "YYYYMMDD_HHMM" format
def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")

# ensures that the parent directory of the given path exists
def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Verzeichnis erstellt: {path.parent}")

# creates dict obj as json file at path
def write_json(path: Path, obj: dict) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:  # "w" = überschreiben statt anhängen
        json.dump(obj, f, ensure_ascii=False, indent=4)
    logger.debug(f"JSON erstellt: {path}")

# loads all yaml files in the given directory and returns a list of dicts
def load_cases(cases_dir: Path) -> list[dict]:
    cases = []
    for f in sorted(cases_dir.glob("*.yaml")):
        with f.open("r", encoding="utf-8") as h:
            data = yaml.safe_load(h)
            data["_file"] = f.name
            cases.append(data)
    logger.debug(f"Testfall-Dateien geladen: {len(cases)}")
    return cases

def count_characters(text: str) -> int:
    # Zählt die Zeichen in einer Antwort
    return len(text) if text else 0

def get_model_aliases(shortform: str) -> str:
    # Mappt Kurzbezeichnungen auf vollständige Modell-IDs
    MODEL_ALIASES = {
        "gpt": "gpt-5-2025-08-07",
        "claude": "claude-sonnet-4-20250514",
        "google": "gemini-2.5-pro",
    }
    return MODEL_ALIASES.get(shortform.lower(), shortform)

def get_model_list(model:str) -> list[str]:
    # Erstellt Model_List aus kommaseparierten Kurzbezeichnungen
    model_list = []
    for m in model.split(","):
        m = m.strip()
        if not m:
            continue
        model_list.append(get_model_aliases(m))
    return model_list

def add_metadata_to_row(row, case, model, t0, raw):
    # Fügt Metadaten zum Ergebnis hinzu
    row["_source_file"] = case["_file"]
    row["_model"] = model
    row["_duration_seconds"] = round(time.perf_counter() - t0, 3)
    row["_response_char_count"] = count_characters(raw)
    return row

def normalize_model_name(model_name: str) -> str:
    # Entfernt Versionsnummern und unerwünschte Zeichen aus dem Modellnamen für Dateinamen
    normalized_model_name = re.sub(r'[-_](\d{4,}([-.]\d{2,})*)$', '', model_name)
    return normalized_model_name