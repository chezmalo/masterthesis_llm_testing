#!/usr/bin/env sh
set -eu
# checks virtual environment 
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
# install dependencies
pip install -e .
python run_tests.py --model "gpt-5-2025-08-07" --cases "src/cases" --out "outputs" --limit 1