#!/bin/bash
cd "$(dirname "$0")"
source .venv_xy_runner/bin/activate
python3 xy_runner.py "$@"
