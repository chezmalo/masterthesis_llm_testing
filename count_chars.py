import os
import json

def average_chars_in_jsons(folder_path: str):
    total_chars = 0
    file_count = 0

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    total_chars += len(content)
                    file_count += 1
            except Exception as e:
                print(f"Fehler beim Lesen von {filename}: {e}")

    if file_count == 0:
        print("Keine JSON-Dateien gefunden.")
        return

    average = total_chars / file_count
    print(f"Anzahl Dateien: {file_count}")
    print(f"Gesamtanzahl Zeichen: {total_chars}")
    print(f"Durchschnitt pro Datei: {average:.2f}")

if __name__ == "__main__":
    ordner = "outputs/final_experiment/claude-sonnet-4"  # Pfad hier anpassen
    average_chars_in_jsons(ordner)
