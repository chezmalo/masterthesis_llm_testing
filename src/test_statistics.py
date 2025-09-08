def init_stats(model_list):
     # Initialisiert das Statistik-Dictionary für die Modelle
    return {model: {"char_counts": [], "durations": []} for model in model_list}

def print_model_statistics(model_list, stats):
    # Statistik pro Modell berechnen und ausgeben
    print("\n=== Modell-Statistiken ===")
    for model in model_list:
        char_counts = stats[model]["char_counts"]
        durations = stats[model]["durations"]
        avg_chars = round(sum(char_counts) / len(char_counts), 2) if char_counts else 0
        avg_duration = round(sum(durations) / len(durations), 3) if durations else 0
        
        # Zeit pro 100 Zeichen berechnen
        avg_time_per_100_chars = round((sum(durations) / sum(char_counts)) * 100, 3) if sum(char_counts) > 0 else 0
        print(f"Modell: {model}")
        print(f"  Durchschnittliche Zeichenanzahl: {avg_chars}")
        print(f"  Durchschnittliche Dauer (Sekunden): {avg_duration}")
        print(f"  Durchschnittliche Zeit pro 100 Zeichen (Sekunden): {avg_time_per_100_chars}")
        print(f"  Anzahl Antworten: {len(char_counts)}")
        print("")
