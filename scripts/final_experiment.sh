#!/usr/bin/env sh
set -eu
# checks virtual environment 
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
# install dependencies
pip install -e .
clear
python3 run_tests.py --model gpt,claude,google --cases src/cases --out output/final_experiment --loglevel INFO --logfile --concurrency 8 --repeat 3