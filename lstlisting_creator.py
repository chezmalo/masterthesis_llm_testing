import os
import re
import unicodedata

# Mapping für Modelle (Langname → Kurzform)
MODEL_MAP = {
    "GPT-5": ("GPT-5", "gpt"),
    "GEMINI-2.5-PRO": ("Gemini 2.5 Pro", "gemini"),
    "CLAUDE-SONNET-4": ("Claude Sonnet 4", "claude"),
}

# Mapping für Prompts mit Sortierwert
PROMPT_MAP = {
    "PROMPT1": ("Hauptdurchlauf", 1, "prompt1"),
    "PROMPT2": ("Konsistenzdurchlauf", 2, "prompt2"),
    "PROMPT3": ("Robustheitsdurchlauf", 3, "prompt3"),
}

# Regex zum Parsen der Dateinamen
FILENAME_REGEX = re.compile(
    r"RESULTS_(?P<model>[^_]+)_CASE(?P<case>\d+)_REPEAT\d+_(?P<prompt>PROMPT\d)_.*\.json"
)

# Replacement map for LaTeX-unsafe symbols
REPLACEMENTS = {
    "\u00A4": "(currency)",  # ¤
    "\u00D7": "x",           # ×
    "\u2205": "empty",       # ∅
    "\u2264": "<=",          # ≤
    "\u2192": "->",          # →
    "\u2011": "-",           # NON-BREAKING HYPHEN
    "\u2013": "-",           # EN DASH
    "\u2212": "-",           # MINUS SIGN
    "\u2026": "...",         # ELLIPSIS …
    "\u2018": "'",           # ‘
    "\u201A": ",",           # ‚
    "\u201C": '"',           # “
    "\u201E": '"',           # „
}


def sanitize_text(s: str) -> str:
    """Replace problematic symbols with ASCII-safe equivalents."""
    for bad, repl in REPLACEMENTS.items():
        s = s.replace(bad, repl)
    return s

def process_directory(base_dir: str):
    for root, dirs, files in os.walk(base_dir):
        json_files = [f for f in files if f.endswith(".json")]
        if not json_files:
            continue

        # Tex-Datei pro Unterordner
        output_path = os.path.join(root, f"{os.path.basename(root)}.tex")
        entries = []

        for json_file in json_files:
            match = FILENAME_REGEX.match(json_file)
            if not match:
                print(f"Überspringe unpassende Datei: {json_file}")
                continue

            model_key = match.group("model")
            case_number = int(match.group("case"))
            prompt_key = match.group("prompt")

            model_name, model_short = MODEL_MAP.get(model_key, (model_key, model_key.lower()))
            prompt_label, prompt_order, prompt_short = PROMPT_MAP.get(
                prompt_key, (prompt_key, 99, prompt_key.lower())
            )

            # JSON-Inhalt laden (falls fehlerhaft → ersetzen)
            json_path = os.path.join(root, json_file)
            with open(json_path, "r", encoding="utf-8", errors="replace") as jf:
                json_content = jf.read().strip()

            # Sanitize JSON content for LaTeX
            json_content = sanitize_text(json_content)

            subsubcaption = f"Ausgabe von {model_name} Anwendungsfall {case_number} {prompt_label}"
            subsublabel = f"{model_short}_case{case_number}_{prompt_short}"
            caption = f"Ausgabe: {model_name} Anwendungsfall {case_number} {prompt_label}"
            label = f"{model_short}_case{case_number}_{prompt_short}"

            # Store all relevant info per entry
            entries.append((case_number, prompt_order, subsubcaption, subsublabel, caption, label, json_content))

        # Sortieren nach Case, dann Prompt-Reihenfolge
        entries.sort(key=lambda x: (x[0], x[1]))

        # Schreiben
        with open(output_path, "w", encoding="utf-8") as out_file:
            for case_number, prompt_order, subsubcaption, subsublabel, caption, label, json_content in entries:
                out_file.write(
                    f"\\subsubsection{{{subsubcaption}}}\\label{{anhang:subsubsec:{subsublabel}}}\n"
                )
                out_file.write(f"\\begin{{lstlisting}}[caption={{{caption}}},label={{{label}}}]\n")
                out_file.write(json_content + "\n")
                out_file.write("\\end{lstlisting}\n\n")

        print(f"Fertig: {output_path}")


if __name__ == "__main__":
    process_directory("outputs/final_experiment")