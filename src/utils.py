from pathlib import Path
import json
from datetime import datetime
import yaml

# gives current timestamp in "YYYYMMDD_HHMM" format
def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")

# ensures that the parent directory of the given path exists
def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

# creates dict obj as json file at path
def write_jsonl(path: Path, obj: dict) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=4) + "\n")

# loads all yaml files in the given directory and returns a list of dicts
def load_cases(cases_dir: Path) -> list[dict]:
    cases = []
    for f in sorted(cases_dir.glob("*.yaml")):
        with f.open("r", encoding="utf-8") as h:
            data = yaml.safe_load(h)
            data["_file"] = f.name
            cases.append(data)
    return cases
