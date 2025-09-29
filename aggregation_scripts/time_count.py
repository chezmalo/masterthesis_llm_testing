import json
import os
from pathlib import Path

def average_duration(subfolder_path):
    subfolder = Path(subfolder_path)
    json_files = list(subfolder.glob("*.json"))
    
    durations = []
    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "_duration_seconds" in data:
                durations.append(data["_duration_seconds"])
    
    if not durations:
        print("Keine _duration_seconds gefunden.")
        return None
    
    total = sum(durations)
    average = total / 30  # fest auf 30 Dateien
    print(f"Summe der Zeiten: {total:.3f} Sekunden")
    print(f"Durchschnitt (geteilt durch 30): {average:.3f} Sekunden")
    return average

# Beispielaufruf:
# average_duration("pfad/zum/unterordner")
if __name__ == "__main__":
    ordner = "outputs/time_measurements/claude-sonnet-4"  # Pfad hier anpassen
    average_duration(ordner)