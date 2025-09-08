#!/usr/bin/env sh
set -eu
# checks virtual environment 
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
# install dependencies
pip install -e .
clear
python run_tests.py --model "google" --cases "src/cases" --out "outputs" --limit 1