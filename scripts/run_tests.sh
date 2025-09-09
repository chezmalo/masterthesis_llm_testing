#!/usr/bin/env sh
set -eu
# checks virtual environment 
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
# installs dependencies
pip install -e .
clear
python run_experiments.py --model "gpt" --input "inputs" --output "outputs" --limit 1