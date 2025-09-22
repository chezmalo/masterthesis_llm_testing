import json
from pathlib import Path
import sys

def prettify_json(file_path: str, indent: int = 4):
    path = Path(file_path)

    # JSON einlesen
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Als pretty JSON zurückschreiben
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

    print(f"{file_path} wurde formatiert.")

def format_jsons_in_directory(directory: str, indent: int = 4):
    dir_path = Path(directory)
    for json_file in dir_path.glob("*.json"):
        prettify_json(str(json_file), indent=indent)

if __name__ == "__main__":
    # Hardcoded directory path
    directory = "outputs/final_experiment/gpt-5"
    indent = 4
    format_jsons_in_directory(directory, indent)