import asyncio
import time
import re
from pathlib import Path
from llm_schema_prompts.llm_output_format import LLMAnswer
from utils.utils import now_stamp, write_json, load_cases, add_metadata_to_row, normalize_model_name
from src.utils.logger import setup
from src.runner.llm_runner import async_prompt_llm, ping_llm, parse_answer, build_user_prompt
from src.llm_schema_prompts.model_prompts import FIX_JSON_PROMPT
from src.test_statistics import print_model_statistics, init_stats

async def _run_async(
    ping: bool,
    model_list: list[str],
    cases: str,
    limit: int | None,
    out: str,
    loglevel: str,
    logfile: bool,
    concurrency: int,
    repeat: int,
    prompt_configs: list[dict], 
    stream: bool = False,  
):
    logger = setup(level=loglevel, write_file=logfile)
    logger.info("LLM Runner gestartet")
    logger.info(f"Verwendete Modelle: {model_list}")

    # Statistikdaten pro Modell
    stats = init_stats(model_list)

    # Ping-Check: Wenn --ping gesetzt ist, führe nur einen kurzen Test-Request aus und beende das Programm
    if ping is True:
        logger.info("Führe LLM-Ping durch...")
        ping_llm()
        return

    cases_dir = Path(cases)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create output folders for each model
    model_output_dirs = {}
    for model in model_list:
        model_name = normalize_model_name(model)
        model_folder = out_dir / model_name
        model_folder.mkdir(parents=True, exist_ok=True)
        model_output_dirs[model] = model_folder

    logger.info("Starte Verarbeitung der Testfälle...")

    # Fälle laden und nacheinander verarbeiten
    cases_list = []
    try:
        cases_list = load_cases(cases_dir)
        logger.info(f"{len(cases_list)} Fälle aus {cases_dir} geladen.")
    except Exception as e:
        logger.error(f"Fehler beim Laden der Testfälle: {e}")
        raise

    # Limit, wenn nicht alle Fälle getestet werden sollen
    if limit is not None and limit > 0:
        logger.info(f"Limit gesetzt: {limit}. Es werden nur die ersten {limit} Fälle verarbeitet.")
        cases_list = cases_list[:limit]

    logger.info(f"Starte {len(cases_list)*len(model_list)*repeat} Fälle")

    sem = asyncio.Semaphore(concurrency)

    # Loop over prompt configs
    for prompt_idx, prompt_config in enumerate(prompt_configs):
        logger.info(f"Running with prompt config {prompt_idx+1}/{len(prompt_configs)}")
        system_prompt = prompt_config["system_prompt"]
        user_prompt = prompt_config["user_prompt_builder"]

        # Asynchrone Funktion zur Verarbeitung eines einzelnen Falls
        async def process_case(case, model, out_dir, logger, repeatcount):
            t0 = time.perf_counter()
            logger.info(f"Starte Fall {case.get('id', 'unbekannt')} mit Modell: {model}")
            async with sem:
                try:
                    # Build prompt, call LLM, parse and validate response
                    logger.debug(f"Verarbeite Fall: {case.get('id', 'unbekannt')} mit Modell: {model}")
                    built_user_prompt = build_user_prompt(case, user_prompt)  # use builder from config
                    logger.debug(f"User-Prompt erstellt für Fall {case.get('id', 'unbekannt')}.")
                    raw = await async_prompt_llm(model, system_prompt, built_user_prompt, stream=stream)
                    logger.debug(f"Rohantwort vom LLM erhalten für Fall {case.get('id', 'unbekannt')}.")
                    try:
                        parsed = parse_answer(raw)
                        logger.debug(f"Antwort geparst und validiert für Fall {case.get('id', 'unbekannt')}.")
                        # Ergebnis + Quelldatei speichern
                        row = parsed.model_dump()
                        row = add_metadata_to_row(row, case, model, t0, raw)
                    except Exception as e:
                        # Versuche, die Antwort mit einem Korrektur-Prompt zu reparieren
                        fix_prompt = FIX_JSON_PROMPT.format(raw_response=raw, schema_json=LLMAnswer.json_schema_str())
                        logger.info(f"Versuche, die Antwort mit einem Korrektur-Prompt zu reparieren für Fall {case.get('id', 'unbekannt')}.")
                        # Korrektur-Prompt an LLM senden
                        raw_fixed = await async_prompt_llm(model, system_prompt, fix_prompt, stream=stream)
                        parsed = parse_answer(raw_fixed)
                        logger.debug(f"Reparierte Antwort geparst und validiert für Fall {case.get('id', 'unbekannt')}.")
                        # Ergebnis + Quelldatei speichern
                        row = parsed.model_dump()
                        row["_correction_attempted"] = True
                        row = add_metadata_to_row(row, case, model, t0, raw)
                        
                    # Statistikdaten sammeln
                    stats[model]["char_counts"].append(row["_response_char_count"])
                    stats[model]["durations"].append(row["_duration_seconds"])

                    # Output-Dateinamen mit Case-Name und Modell generieren
                    case_name: str = Path(case["_file"]).stem
                    model_name: str = normalize_model_name(model)
                    model_folder = model_output_dirs[model]
                    out_file = model_folder / f"RESULTS_{model_name.upper()}_{case_name.upper()}_REPEAT{str(repeatcount)}_PROMPT{prompt_idx+1}_{now_stamp()}.json"
                    write_json(out_file, row)
                    logger.info(f"[OK] {case['id']} -> gespeichert in {out_file} "
                                f"({row['_duration_seconds']}s, {row['_response_char_count']} Zeichen)")
                except Exception as e:
                    # Fehler speichern (z.B. Fehler der YAML-Datei, JSON-Parsing-Fehler, Validierungsfehler)
                    duration = round(time.perf_counter() - t0, 3)
                    logger.error(f"Fehler bei Fall {case.get('id')}: {e} (nach {duration}s)")
                    # Use model-specific output folder for errors as well
                    model_folder = model_output_dirs.get(model, out_dir)
                    out_file = model_folder / f"error_results_{case.get('id', 'unknown')}_{model}_PROMPT{prompt_idx+1}_{now_stamp()}.json"
                    write_json(out_file, {"case_id": case.get("id"), "error": str(e)})

        # Run all cases for all models and repeat as many times as specified
        tasks = [
            process_case(case, model, out_dir, logger, repeatcount)
            for model in model_list
            for case in cases_list
            for repeatcount in range(repeat)
        ]
        await asyncio.gather(*tasks)

    print_model_statistics(model_list, stats, out_dir)