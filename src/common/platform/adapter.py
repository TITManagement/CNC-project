"""
プラットフォーム依存の処理をまとめたアダプター。
"""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple


class EnvironmentAdapter:
    """
    CLI からテストまで同じ API で環境依存処理を扱うためのアダプター。

    input_func を差し替えられるようにしておくと、対話入力が必要なケースを
    テストでモックしやすい。
    """

    def __init__(self, *, input_func: Optional[Callable[[str], str]] = None):
        self._input = input_func or input

    def get_platform_info(self) -> dict:
        system = platform.system().lower()
        return {
            "system": system,
            "is_windows": system == "windows",
            "is_macos": system == "darwin",
            "is_linux": system == "linux",
            "version": platform.version(),
            "machine": platform.machine(),
        }

    def get_default_serial_ports(self) -> Sequence[str]:
        info = self.get_platform_info()
        if info["is_windows"]:
            return ["COM1", "COM2", "COM3", "COM4", "COM5"]
        if info["is_macos"]:
            return [
                "/dev/tty.usbserial-*",
                "/dev/tty.usbmodem*",
                "/dev/cu.usbserial-*",
            ]
        return ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"]

    def normalize_path(self, path_str: str) -> str:
        return str(Path(path_str).expanduser().resolve())

    def get_venv_activate_command(self) -> str:
        if self.get_platform_info()["is_windows"]:
            return ".venv\\Scripts\\activate.bat"
        return "source .venv/bin/activate"

    def get_python_executable(self) -> str:
        if self.get_platform_info()["is_windows"]:
            return "python.exe"
        return "python3"

    def select_file_dialog(
        self,
        title: str,
        filetypes: Sequence[Tuple[str, str]],
        *,
        initialdir: Optional[str] = None,
    ) -> str:
        """
        ファイルダイアログを表示してパスを返す。
        tkinter が使えない場合は標準入力でパスを受け取る。
        """
        try:
            import tkinter as tk
            from tkinter import filedialog
        except ImportError:
            print("tkinterが利用できません。ファイルパスを直接入力してください。")
            return self._input(f"{title}: ").strip()

        root = tk.Tk()
        root.withdraw()

        info = self.get_platform_info()
        if info["is_windows"]:
            root.wm_attributes("-topmost", 1)

        initial_dir = self.normalize_path(initialdir) if initialdir else self.normalize_path(".")
        if not os.path.exists(initial_dir):
            initial_dir = self.normalize_path(".")

        try:
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes,
                initialdir=initial_dir,
            )
        finally:
            root.destroy()
        return file_path


__all__ = ["EnvironmentAdapter"]
