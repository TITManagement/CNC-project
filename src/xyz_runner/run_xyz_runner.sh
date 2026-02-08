#!/bin/bash
cd "$(dirname "$0")"
source .venv_xyz_runner/bin/activate
python3 xyz_runner.py "$@"
