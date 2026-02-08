#!/usr/bin/env python3
"""Environment setup helper (cross-platform).

This script creates/uses a project-local .venv and installs requirements from
requirements.txt if present. It intentionally does NOT run the application.

Usage:
  python env_setup.py         # create/use .venv and install deps
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"


def ensure_venv(venv_path: Path) -> Path:
    if not venv_path.exists():
        print(f"Creating virtualenv at {venv_path}")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def install_requirements(python: Path) -> None:
    req = ROOT / "requirements.txt"
    if req.exists():
        print("Installing requirements from requirements.txt (if needed)...")
        subprocess.check_call([str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
        subprocess.check_call([str(python), "-m", "pip", "install", "-r", str(req)])
    else:
        print("No requirements.txt found — nothing to install.")


def main() -> int:
    python_in_venv = ensure_venv(VENV)
    install_requirements(python_in_venv)
    print("")
    print("Environment ready.")
    print("To run the application, activate the venv and run your command, e.g:")
    if os.name == "nt":
        print(r"  .\.venv\Scripts\activate.bat")
        print(r"  python src\xy_runner\xy_runner.py --config examples\example_xy\SIM_svg_sample.yaml")
    else:
        print("  source .venv/bin/activate")
        print("  python src/xy_runner/xy_runner.py --config examples/example_xy/SIM_svg_sample.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
