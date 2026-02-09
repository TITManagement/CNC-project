"""
CustomTkinter GUI launcher for XY runner.

Allows selecting driver (REAL/SIM), YAML config, and optional SVG override
from a single window and then runs the runner with those selections.
"""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import tkinter.filedialog as fd
import tkinter.font as tkfont

try:
    from .xy_runner import XYRunnerApp
except ImportError:
    # Support direct script execution:
    #   python src/xy_runner/gui_launcher.py
    runner_path = Path(__file__).resolve().with_name("xy_runner.py")
    spec = importlib.util.spec_from_file_location("_xy_runner_module", runner_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"xy_runner.py をロードできません: {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    XYRunnerApp = module.XYRunnerApp

try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:
    ctk = None
    _CTK_IMPORT_ERROR = exc
else:
    _CTK_IMPORT_ERROR = None


class RunnerGUI(ctk.CTk if ctk else object):
    def __init__(self):
        super().__init__()
        self.title("XY Runner Launcher")
        self.geometry("600x320")
        self._apply_default_font()

        self.driver_var = ctk.StringVar(value="sim")
        self.yaml_var = ctk.StringVar()
        self.svg_var = ctk.StringVar()
        self.yaml_name = ctk.StringVar(value="(not selected)")
        self.yaml_dir = ctk.StringVar(value="")
        self.svg_name = ctk.StringVar(value="(not selected)")
        self.svg_dir = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="Ready")

        self._build_widgets()

    def _build_widgets(self):
        padding = {"padx": 12, "pady": 8}

        # Driver selection
        driver_frame = ctk.CTkFrame(self)
        driver_frame.pack(fill="x", **padding)
        ctk.CTkLabel(driver_frame, text="Driver").pack(side="left", padx=8)
        for text, value in [("SIM (simulation)", "sim"), ("REAL (physical)", "chuo")]:
            ctk.CTkRadioButton(driver_frame, text=text, variable=self.driver_var, value=value).pack(
                side="left", padx=4
            )

        # YAML selection
        yaml_frame = ctk.CTkFrame(self)
        yaml_frame.pack(fill="x", **padding)
        ctk.CTkLabel(yaml_frame, text="YAML config").pack(side="left", padx=8)
        ctk.CTkEntry(yaml_frame, textvariable=self.yaml_var, width=360).pack(side="left", padx=4, expand=True, fill="x")
        ctk.CTkButton(yaml_frame, text="Browse", command=self._browse_yaml).pack(side="left", padx=4)
        yaml_info = ctk.CTkFrame(self)
        yaml_info.pack(fill="x", padx=20, pady=0)
        ctk.CTkLabel(yaml_info, textvariable=self.yaml_name, anchor="w").pack(side="left")
        ctk.CTkLabel(yaml_info, textvariable=self.yaml_dir, anchor="w", text_color="gray").pack(
            side="left", padx=8
        )

        # SVG override selection
        svg_frame = ctk.CTkFrame(self)
        svg_frame.pack(fill="x", **padding)
        ctk.CTkLabel(svg_frame, text="SVG/G-code (optional)").pack(side="left", padx=8)
        ctk.CTkEntry(svg_frame, textvariable=self.svg_var, width=360).pack(side="left", padx=4, expand=True, fill="x")
        ctk.CTkButton(svg_frame, text="Browse", command=self._browse_svg).pack(side="left", padx=4)
        svg_info = ctk.CTkFrame(self)
        svg_info.pack(fill="x", padx=20, pady=0)
        ctk.CTkLabel(svg_info, textvariable=self.svg_name, anchor="w").pack(side="left")
        ctk.CTkLabel(svg_info, textvariable=self.svg_dir, anchor="w", text_color="gray").pack(
            side="left", padx=8
        )

        # Run button and status
        run_frame = ctk.CTkFrame(self)
        run_frame.pack(fill="x", **padding)
        ctk.CTkButton(run_frame, text="Run", command=self._run_runner).pack(side="left", padx=8)
        ctk.CTkLabel(run_frame, textvariable=self.status_var, anchor="w").pack(side="left", padx=8, expand=True, fill="x")

    def _apply_default_font(self) -> None:
        """日本語を含むデフォルトフォントを優先して設定する。"""
        try:
            families = set(tkfont.families(self))
            default_font = tkfont.nametofont("TkDefaultFont")
        except Exception:
            families = set()
            default_font = None
        for family in (
            "Hiragino Sans",
            "Hiragino Kaku Gothic ProN",
            "Noto Sans CJK JP",
            "Yu Gothic UI",
            "Yu Gothic",
            "Arial Unicode MS",
        ):
            if family in families:
                if default_font is not None:
                    default_font.configure(family=family, size=12)
                break

    def _browse_yaml(self):
        path = fd.askopenfilename(title="Select YAML config", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        if path:
            self._set_path(self.yaml_var, self.yaml_name, self.yaml_dir, path)

    def _browse_svg(self):
        path = fd.askopenfilename(title="Select SVG/G-code file", filetypes=[("SVG/G-code", "*.svg *.gcode *.nc"), ("All files", "*.*")])
        if path:
            self._set_path(self.svg_var, self.svg_name, self.svg_dir, path)

    def _run_runner(self):
        yaml_path = self._normalize_path(self.yaml_var.get())
        svg_path = self._normalize_path(self.svg_var.get()) if self.svg_var.get().strip() else None
        driver = self.driver_var.get()

        if not yaml_path or not Path(yaml_path).exists():
            self.status_var.set("YAML is missing or not found")
            return

        self.status_var.set("Running... (UI is locked until done)")
        self.update_idletasks()
        try:
            args = SimpleNamespace(
                config=str(yaml_path),
                driver=driver,
                show=True,
                no_animate=False,
                debug=False,
            )
            app = XYRunnerApp(args)
            # Matplotlib GUI must run on the main thread; block here
            app.run(svg_override=svg_path)
            self.status_var.set("Done")
        except Exception as exc:  # pragma: no cover - GUI runtime
            self.status_var.set(f"Error: {exc}")

    @staticmethod
    def _normalize_path(path_str: str) -> Optional[Path]:
        if not path_str or not path_str.strip():
            return None
        return Path(path_str).expanduser().resolve()

    @staticmethod
    def _set_path(target_var: ctk.StringVar, name_var: ctk.StringVar, dir_var: ctk.StringVar, path: str) -> None:
        target_var.set(path)
        p = Path(path).expanduser().resolve()
        name_var.set(p.name)
        dir_var.set(str(p.parent))


def main():
    if ctk is None:
        print(
            "customtkinter が未導入です。GUIを使うには `pip install -e \".[gui]\"` "
            "または `pip install customtkinter` を実行してください。"
        )
        raise SystemExit(1) from _CTK_IMPORT_ERROR
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = RunnerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
