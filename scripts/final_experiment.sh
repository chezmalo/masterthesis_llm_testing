#!/usr/bin/env sh
set -eu
# checks virtual environment 
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
# install dependencies
pip install -e .
clear
python3 run_experiments.py --model gpt,claude,google --input inputs --output outputs/time_measurements --loglevel INFO --logfile --concurrency 1 --repeat 1 --no-stream