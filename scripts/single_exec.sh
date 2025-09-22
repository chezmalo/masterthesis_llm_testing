#!/usr/bin/env sh
set -eu
# checks virtual environment 
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
# install dependencies
pip install -e .
clear
python3 run_experiments.py --model gpt --input inputs/single_exec --output outputs/final_experiment --loglevel INFO --logfile --concurrency 1 --repeat 1