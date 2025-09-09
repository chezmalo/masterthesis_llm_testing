@echo off
setlocal enabledelayedexpansion

rem venv anlegen
if not exist .venv (
  %PY% -m venv .venv
)

rem venv aktivieren
call .\.venv\Scripts\activate.bat

rem pip upgraden
python -m pip install --upgrade pip

rem dependencies installieren
pip install -e .

rem Konsole clearn
cls

rem Tests starten
python run_experiments.py --model gpt,claude,google --input inputs --output output\final_experiment --loglevel INFO --logfile --concurrency 8 --repeat 3

endlocal
