"""
CustomTkinter GUI launcher for XYZ runner.
Select driver, YAML config (optional), and G-code/STEP file from one window.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import tkinter.filedialog as fd

# Tk ベースGUIと整合するバックエンドを優先し、macOS 固有 backend の
# バイナリ互換エラーを回避する。
os.environ.setdefault("MPLBACKEND", "TkAgg")

try:
    from .xyz_runner import XYZRunnerApp
except ImportError:
    # Support direct script execution:
    #   python src/xyz_runner/gui_launcher.py
    runner_path = Path(__file__).resolve().with_name("xyz_runner.py")
    spec = importlib.util.spec_from_file_location("_xyz_runner_module", runner_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"xyz_runner.py をロードできません: {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    XYZRunnerApp = module.XYZRunnerApp

try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:
    ctk = None
    _CTK_IMPORT_ERROR = exc
else:
    _CTK_IMPORT_ERROR = None


class XYZRunnerGUI(ctk.CTk if ctk else object):
    def __init__(self):
        super().__init__()
        self.title("XYZ Runner Launcher")
        self.geometry("640x320")

        self.driver_var = ctk.StringVar(value="sim")
        self.yaml_var = ctk.StringVar()
        self.file_var = ctk.StringVar()
        self.yaml_name = ctk.StringVar(value="(未選択)")
        self.yaml_dir = ctk.StringVar(value="")
        self.file_name = ctk.StringVar(value="(未選択)")
        self.file_dir = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="準備完了")

        self._build()

    def _build(self):
        padding = {"padx": 12, "pady": 8}

        # Driver selection
        frame_driver = ctk.CTkFrame(self)
        frame_driver.pack(fill="x", **padding)
        ctk.CTkLabel(frame_driver, text="ドライバ").pack(side="left", padx=8)
        for text, val in [("SIM (シミュレーション)", "sim"), ("REAL (Chuo)", "chuo")]:
            ctk.CTkRadioButton(frame_driver, text=text, variable=self.driver_var, value=val).pack(
                side="left", padx=6
            )

        # YAML selection
        frame_yaml = ctk.CTkFrame(self)
        frame_yaml.pack(fill="x", **padding)
        ctk.CTkLabel(frame_yaml, text="YAML 設定").pack(side="left", padx=8)
        ctk.CTkEntry(frame_yaml, textvariable=self.yaml_var, width=380).pack(
            side="left", padx=6, expand=True, fill="x"
        )
        ctk.CTkButton(frame_yaml, text="参照", command=self._browse_yaml).pack(side="left", padx=4)
        yaml_info = ctk.CTkFrame(self)
        yaml_info.pack(fill="x", padx=20, pady=0)
        ctk.CTkLabel(yaml_info, textvariable=self.yaml_name, anchor="w").pack(side="left")
        ctk.CTkLabel(yaml_info, textvariable=self.yaml_dir, anchor="w", text_color="gray").pack(
            side="left", padx=8
        )

        # File selection (gcode/step)
        frame_file = ctk.CTkFrame(self)
        frame_file.pack(fill="x", **padding)
        ctk.CTkLabel(frame_file, text="G-code/STEP").pack(side="left", padx=8)
        ctk.CTkEntry(frame_file, textvariable=self.file_var, width=380).pack(
            side="left", padx=6, expand=True, fill="x"
        )
        ctk.CTkButton(frame_file, text="参照", command=self._browse_job_file).pack(side="left", padx=4)
        file_info = ctk.CTkFrame(self)
        file_info.pack(fill="x", padx=20, pady=0)
        ctk.CTkLabel(file_info, textvariable=self.file_name, anchor="w").pack(side="left")
        ctk.CTkLabel(file_info, textvariable=self.file_dir, anchor="w", text_color="gray").pack(
            side="left", padx=8
        )

        # Run and status
        frame_run = ctk.CTkFrame(self)
        frame_run.pack(fill="x", **padding)
        ctk.CTkButton(frame_run, text="実行", command=self._run).pack(side="left", padx=8)
        ctk.CTkLabel(frame_run, textvariable=self.status_var, anchor="w").pack(
            side="left", padx=8, expand=True, fill="x"
        )

    def _browse_yaml(self):
        path = fd.askopenfilename(title="YAML設定ファイルを選択", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        if path:
            self._set_path(self.yaml_var, self.yaml_name, self.yaml_dir, path)

    def _browse_job_file(self):
        path = fd.askopenfilename(
            title="G-codeまたはSTEPファイルを選択",
            filetypes=[
                ("G-code files", "*.gcode *.nc *.tap"),
                ("STEP files", "*.stp *.step"),
                ("All supported", "*.gcode *.nc *.tap *.stp *.step"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._set_path(self.file_var, self.file_name, self.file_dir, path)

    def _run(self):
        yaml_path = self._normalize(self.yaml_var.get())
        job_path = self._normalize(self.file_var.get())
        driver = self.driver_var.get()

        if not yaml_path or not yaml_path.exists():
            self.status_var.set("YAMLが未指定または存在しません")
            return
        self.status_var.set("実行中...（完了までお待ちください）")
        self.update_idletasks()
        try:
            args = SimpleNamespace(
                config=str(yaml_path),
                driver=driver,
                show=True,
                no_animate=False,
                debug=False,
                file=None,
            )
            app = XYZRunnerApp(args)
            app.run(file_override=str(job_path) if job_path else None)
            self.status_var.set("完了")
        except Exception as exc:  # pragma: no cover - GUI runtime
            self.status_var.set(f"エラー: {exc}")

    @staticmethod
    def _normalize(p: str) -> Optional[Path]:
        if not p or not p.strip():
            return None
        return Path(p).expanduser().resolve()

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
    app = XYZRunnerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
