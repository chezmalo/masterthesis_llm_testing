#!/usr/bin/env sh
set -eu
# checks virtual environment 
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
# install dependencies
pip install -e .
python run_experiments.py --model "google/gemini-2.0-pro" --cases "src/cases" --out "outputs"