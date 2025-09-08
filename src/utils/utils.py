import logging
from pathlib import Path
from datetime import datetime
import json
import yaml

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
