#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config-driven XYZ runner (3D) - Cross-platform support
- Platforms: Windows, macOS, Linux (Ubuntu 24.04)
- Drivers: sim / chuo (XYZ)
- Jobs: grid_spheres, gcode, stp
Dependencies:
  pip install pyyaml matplotlib pyserial numpy svgpathtools pythonocc-core
"""
import argparse
import logging
import math
import os
import sys
from pathlib import Path
from typing import Mapping, Optional
import matplotlib.pyplot as plt

from common.drivers import CncDriver, ChuoDriver
from common.gcode import LinearGCodeInterpreter, ModalState3D
from common.jobs import Job, JobFactory
from common.platform import EnvironmentAdapter
from common.runtime import ConfigLoader, JobDispatcher, VisualizationController

SRC_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = SRC_DIR.parent
src_str = str(SRC_DIR)
if src_str in sys.path:
    sys.path.remove(src_str)
sys.path.insert(0, src_str)



def _resolve_resource_path(file_entry: str, context: Mapping[str, object]) -> Path:
    path = Path(file_entry).expanduser()
    if path.is_absolute():
        return path

    # allow configs to refer to drawing_data/foo.ext regardless of current dir
    parts = path.parts
    tail_after_data_dir = None
    if "drawing_data" in parts:
        idx = parts.index("drawing_data")
        tail_after_data_dir = Path(*parts[idx + 1 :]) if idx + 1 < len(parts) else Path(".")

    config_dir = Path(context.get("config_dir", Path.cwd()))
    project_root = Path(context.get("project_root", config_dir))
    candidates = []
    for base in (
        config_dir,
        config_dir.parent,
        project_root,
        project_root / "drawing_data",
        project_root / "drawing_data" / "example_xyz",
    ):
        if base and base not in candidates:
            candidates.append(base)

    relative_targets = [path]
    if tail_after_data_dir:
        relative_targets.append(tail_after_data_dir)

    for rel in relative_targets:
        for base in candidates:
            candidate = (base / rel).resolve()
            if candidate.exists():
                return candidate
    return (config_dir / path).resolve()


# ========= 共通（簡易Gコードラッパ：直線/円弧/3D） =========
class GCodeWrapper3D(LinearGCodeInterpreter):
    modal_state_cls = ModalState3D
    linear_axes = ("X", "Y", "Z")
    extra_params = ("I", "J", "K")
    motion_g_codes = (0, 1)

    def _handle_extended_motion(self, gcode, params, words):
        super()._handle_extended_motion(gcode, params, words)


class GcodeFileJob(Job):
    """G-code ファイルを実行するジョブ。"""

    def execute(self, *, gcode, context=None):
        context = context or {}
        file_entry = self.config.get("file")
        if not file_entry:
            print("G-codeファイルが指定されていません。")
            return
        file_path = _resolve_resource_path(str(file_entry), context)
        if not file_path or str(file_path).strip() == "":
            print("G-codeファイルが指定されていません。")
            return
        if not file_path.exists():
            print(f"G-codeファイル '{file_path}' が見つかりません")
            return
        print(f"実行中: gcode ジョブ - {file_path}")
        with file_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                gcode.exec(line)
        print(f"G-codeファイル '{file_path}' を実行しました")


class StepFileJob(Job):
    """STEP ファイルを簡易処理するジョブ。"""

    def execute(self, *, gcode, context=None):
        context = context or {}
        file_entry = self.config.get("file")
        if not file_entry:
            print("STEPファイルが指定されていません。")
            return
        file_path = _resolve_resource_path(str(file_entry), context)
        if not file_path or str(file_path).strip() == "":
            print("STEPファイルが指定されていません。")
            return
        if not file_path.exists():
            print(f"STEPファイル '{file_path}' が見つかりません")
            return
        print(f"実行中: stp ジョブ - {file_path}")
        origin = self.config.get("origin", [0, 0, 0])
        resolution = self.config.get("resolution", 0.5)
        process_step_file_simple(gcode, file_path, origin, resolution)
        print(f"STEPファイル '{file_path}' を処理しました（簡易モード）")


class GridSpheresJob(Job):
    """3D グリッド球体パターンを描画するジョブ。"""

    def execute(self, *, gcode, context=None):
        defaults = (context or {}).get("defaults", {})
        origin = self.config.get("origin", [0, 0, 0])
        area = self.config.get("area", [100, 100, 50])
        cell = float(self.config.get("cell", 20))
        sphere_d = float(self.config.get("sphere_d", 15))
        feed = float(self.config.get("feed", defaults.get("feed", 1000)))
        grid_spheres_3d(gcode, origin, area, cell, sphere_d, feed)
        print(f"3Dグリッド球体パターンを実行しました (cell={cell}mm, sphere_d={sphere_d}mm)")


def build_xyz_job_factory() -> JobFactory:
    factory = JobFactory()
    factory.register("gcode", lambda cfg: GcodeFileJob(cfg))
    factory.register("stp", lambda cfg: StepFileJob(cfg))
    factory.register("grid_spheres", lambda cfg: GridSpheresJob(cfg))
    return factory


class XYZRunnerApp:
    """XYZ ランナー全体のオーケストレーションを担当。"""

    def __init__(self, args, env: Optional[EnvironmentAdapter] = None):
        self.args = args
        self.env = env or EnvironmentAdapter()
        self._config_loader = ConfigLoader(self._default_config)

    def run(self, *, file_override: Optional[str] = None) -> None:
        selected_file = None
        job_type = None
        config_path: Optional[Path] = None

        if not self.args.config:
            selected_file, job_type = self._prompt_file_selection()
            if not selected_file:
                print("処理を終了します。")
                return
            config_dir = Path(selected_file).resolve().parent
        else:
            config_path = Path(self.args.config)
            config_dir = config_path.resolve().parent

        cfg = self._config_loader.load(
            str(config_path) if config_path else None,
            driver_override=self.args.driver,
        )
        if selected_file:
            cfg["selected_file"] = selected_file
        if file_override:
            cfg["selected_file"] = file_override

        driver = self._create_driver(cfg)
        g = GCodeWrapper3D(driver)
        defaults = cfg.get("defaults", {})
        self._apply_defaults(g, defaults)

        factory = build_xyz_job_factory()
        dispatcher = JobDispatcher(factory)
        context = {
            "defaults": defaults,
            "config_dir": config_dir,
            "project_root": ROOT_DIR,
        }

        if job_type and job_type != "yaml":
            dispatcher.dispatch_job(
                {"type": job_type, "file": cfg.get("selected_file")},
                gcode=g,
                context=context,
            )
        else:
            jobs_prepared = self._ensure_job_resources(cfg.get("jobs", []), context, file_override)
            dispatcher.dispatch_jobs(
                jobs_prepared,
                gcode=g,
                context=context,
            )

        self._process_file_argument(g)

        visual = VisualizationController(
            driver,
            default_title="XYZ Simulation",
            done_message="3D軌跡を表示しました",
            skip_message="軌跡表示をスキップしました（--show または visual.show=true で表示）",
        )
        visual.show(
            cfg_visual=cfg.get("visual", {}),
            force_show=self.args.show,
            disable_animate=self.args.no_animate,
            selected_file=cfg.get("selected_file"),
        )

    def _default_config(self, driver_name):
        return {
            "driver": driver_name or "sim",
            "defaults": {"unit": "mm", "mode": "absolute", "feed": 1000},
            "visual": {
                "show": True,
                "animate": True,
                "fps": 1080,
                "title": "XYZ Runner",
            },
        }

    def _prompt_file_selection(self):
        return select_and_execute_file(self.env)

    def _create_driver(self, cfg):
        driver_name = self.args.driver or cfg.get("driver", "sim")
        if driver_name == "sim":
            return SimDriver3D()

        port = cfg.get("port")
        if not port:
            logging.warning("driver=chuo を選択しましたが port が未設定のためシミュレーションを使用します。")
            return SimDriver3D()

        baud = int(cfg.get("baud", 9600))
        timeout = float(cfg.get("timeout", 1.0))
        write_timeout = float(cfg.get("write_timeout", 1.0))
        accel = int(cfg.get("qt_accel", cfg.get("accel", 100)))
        enable_response = bool(cfg.get("qt_enable_response", True))

        mm_per_pulse_val: Optional[float] = None
        mm_per_pulse = cfg.get("mm_per_pulse")
        if mm_per_pulse is not None:
            try:
                mm_per_pulse_val = float(mm_per_pulse)
            except (TypeError, ValueError):
                logging.warning("mm_per_pulse が数値に変換できません: %s", mm_per_pulse)

        mm_to_device_fn = None
        if callable(mm_per_pulse):
            mm_to_device_fn = mm_per_pulse  # type: ignore[assignment]

        driver = ChuoDriver(
            port=port,
            baudrate=baud,
            timeout=timeout,
            write_timeout=write_timeout,
            mm_per_pulse=mm_per_pulse_val,
            mm_to_device=mm_to_device_fn,
            enable_response=enable_response,
            default_accel=accel,
        )

        driver_settings = cfg.get("driver_settings", {})
        if isinstance(driver_settings, Mapping):
            driver.set_speed_params(
                rapid_speed=driver_settings.get("rapid_speed"),
                cut_speed=driver_settings.get("cut_speed"),
                accel=driver_settings.get("accel"),
            )

        return driver

    def _apply_defaults(self, gcode: GCodeWrapper3D, defaults: dict) -> None:
        if defaults.get("unit", "mm") == "mm":
            gcode.exec("G21")
        else:
            gcode.exec("G20")
        if defaults.get("mode", "absolute") == "absolute":
            gcode.exec("G90")
        else:
            gcode.exec("G91")
        if "feed" in defaults:
            gcode.exec(f"F{float(defaults['feed'])}")

    def _process_file_argument(self, gcode: GCodeWrapper3D) -> None:
        if not self.args.file:
            return
        ftype, fdata = load_gcode_or_stp(self.args.file)
        if ftype == "gcode" and fdata:
            for line in fdata:
                gcode.exec(line)
            print(f"G-codeファイル '{self.args.file}' を実行しました")
        elif ftype == "stp":
            print("STEPファイル形状を取得しました（詳細処理は未実装）")

    def _ensure_job_resources(self, jobs_cfg, context, file_override: Optional[str]):
        """G-code/STEP ジョブでファイルが無い場合はダイアログで選択する。"""
        fixed = []
        for job in jobs_cfg or []:
            job_type = job.get("type")
            if job_type in ("gcode", "stp"):
                file_entry = file_override or job.get("file")
                resolved = _resolve_resource_path(file_entry, context) if file_entry else None
                if not resolved or not resolved.exists():
                    if job_type == "gcode":
                        title = "G-codeファイルを選択してください"
                        types = [("G-code files", "*.gcode *.nc *.tap"), ("All files", "*.*")]
                    else:
                        title = "STEPファイルを選択してください"
                        types = [("STEP files", "*.stp *.step"), ("All files", "*.*")]
                    chosen = select_file_with_dialog(self.env, title, types)
                    if chosen:
                        resolved = Path(chosen).expanduser().resolve()
                if resolved and resolved.exists():
                    job["file"] = str(resolved)
                else:
                    print(f"{job_type} ファイルが指定されず選択もされませんでした。ジョブをスキップします。")
                    continue
            fixed.append(job)
        return fixed


# ========= ドライバ（3Dシミュレーション/実機） =========
class SimDriver3D(CncDriver):
    axes = ("x", "y", "z")

    def __init__(self):
        self.tracks = []  # 移動履歴（(x0,y0,z0,x1,y1,z1,rapid,feed)）
        self._cx = 0.0
        self._cy = 0.0
        self._cz = 0.0

    def set_units_mm(self):
        pass

    def set_units_inch(self):
        pass

    def home(self):
        self._cx = self._cy = self._cz = 0.0

    def move_abs(self, *, feed=None, rapid=False, **axes):
        x_val = axes.get("x")
        y_val = axes.get("y")
        z_val = axes.get("z")
        nx = self._cx if x_val is None else float(x_val)
        ny = self._cy if y_val is None else float(y_val)
        nz = self._cz if z_val is None else float(z_val)
        logging.debug(
            "[DEBUG] SimDriver3D.move_abs: from=(%s,%s,%s) to=(%s,%s,%s), rapid=%s, feed=%s",
            self._cx,
            self._cy,
            self._cz,
            nx,
            ny,
            nz,
            rapid,
            feed,
        )
        self.tracks.append((self._cx, self._cy, self._cz, nx, ny, nz, rapid, feed))
        self._cx, self._cy, self._cz = nx, ny, nz

    def animate_tracks(self, animate=True, fps=1080, title="XYZ Simulation"):
        """
        移動履歴（tracks）を3Dでmatplotlibで可視化
        animate: Trueならアニメーション表示、Falseなら軌跡のみ
        fps: アニメーションのフレームレート
        title: グラフタイトル
        """
        import matplotlib.animation as animation

        if not self.tracks:
            print("No tracks")
            return

        # 座標範囲を計算
        xs = [p for s in self.tracks for p in (s[0], s[3])]
        ys = [p for s in self.tracks for p in (s[1], s[4])]
        zs = [p for s in self.tracks for p in (s[2], s[5])]

        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        zmin, zmax = min(zs), max(zs)
        pad = 0.05 * max(xmax - xmin or 1, ymax - ymin or 1, zmax - zmin or 1)

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")
        ax.set_xlim(xmin - pad, xmax + pad)
        ax.set_ylim(ymin - pad, ymax + pad)
        ax.set_zlim(zmin - pad, zmax + pad)
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        ax.set_zlabel("Z [mm]")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

        if not animate:
            # 静的表示
            done_text = fig.text(
                0.01,
                0.01,
                "",
                color="green",
                ha="left",
                va="bottom",
                fontsize=10,
                alpha=0.9,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.7, edgecolor="green"),
            )
            for x0, y0, z0, x1, y1, z1, rapid, _ in self.tracks:
                ax.plot(
                    [x0, x1],
                    [y0, y1],
                    [z0, z1],
                    ":" if rapid else "-",
                    linewidth=1.2 if rapid else 2.0,
                    alpha=0.8,
                )
            done_text.set_text("DONE")
            plt.show()
            return

        # アニメーション表示
        lines = []
        for _ in self.tracks:
            (ln,) = ax.plot([], [], [], "-", lw=2.0, alpha=0.8)
            lines.append(ln)
        done_text = fig.text(
            0.01,
            0.01,
            "",
            color="green",
            ha="left",
            va="bottom",
            fontsize=10,
            alpha=0.9,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7, edgecolor="green"),
        )

        # 各線分のステップ数を計算
        steps = []
        for x0, y0, z0, x1, y1, z1, rapid, _ in self.tracks:
            dist = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)
            step_count = max(3, int(dist * 2) + 5)  # 距離に応じてステップ数調整
            steps.append(step_count)

        def data_gen():
            last_idx = len(self.tracks) - 1
            for i, (x0, y0, z0, x1, y1, z1, rapid, _) in enumerate(self.tracks):
                n = steps[i]
                for k in range(1, n + 1):
                    t = k / n
                    x = x0 + (x1 - x0) * t
                    y = y0 + (y1 - y0) * t
                    z = z0 + (z1 - z0) * t
                    yield i, [x0, x], [y0, y], [z0, z], rapid, (i == last_idx and k == n)

        def init():
            for ln in lines:
                ln.set_data_3d([], [], [])
            return lines

        def update(data):
            i, xs_, ys_, zs_, rapid, is_done = data
            # 過去の線分を描画（完了済み）
            for j in range(i):
                x0, y0, z0, x1, y1, z1, r, _ = self.tracks[j]
                lines[j].set_data_3d([x0, x1], [y0, y1], [z0, z1])
                lines[j].set_linestyle(":" if r else "-")
                lines[j].set_color("gray" if r else "blue")
            # 現在の線分を描画（進行中）
            if i < len(lines):
                lines[i].set_data_3d(xs_, ys_, zs_)
                lines[i].set_linestyle(":" if rapid else "-")
                lines[i].set_color("red" if rapid else "green")
            if is_done:
                done_text.set_text("DONE")
            return lines

        anim = animation.FuncAnimation(
            fig,
            update,
            frames=data_gen(),
            init_func=init,
            blit=False,
            interval=1000 / fps,
            repeat=False,
            cache_frame_data=False,
        )

        # Keep a reference to the animation to avoid it being garbage-collected
        try:
            fig._anim = anim
        except Exception:
            globals().setdefault("_last_anim", anim)

        plt.show()


# ========= 3Dパターン =========
def grid_spheres_3d(g, origin, area, cell, sphere_d, feed, levels=3):
    """
    3Dグリッド球体パターンを生成（Z=0から開始）
    origin: [x, y, z] 原点座標
    area: [w, h, d] XYZ範囲
    cell: セル間隔
    sphere_d: 球体直径
    feed: 送り速度
    levels: Z方向のレベル数
    """
    ox, oy, oz = origin
    W, H, D = area
    r = sphere_d / 2.0

    g.exec("G21 G90")  # mm, absolute
    g.exec(f"F{feed}")
    g.exec("G0 Z0")  # Z=0から開始

    nx, ny, nz = int(W // cell), int(H // cell), int(D // cell)
    base_cx, base_cy, base_cz = ox + cell / 2.0, oy + cell / 2.0, oz + cell / 2.0

    print(f"3Dグリッド: {nx}x{ny}x{nz} = {nx*ny*nz}個の球体 (Z=0から開始)")

    total_spheres = 0
    for k in range(nz):  # Z方向
        for j in range(ny):  # Y方向
            for i in range(nx):  # X方向
                cx = base_cx + i * cell
                cy = base_cy + j * cell
                cz = base_cz + k * cell

                logging.debug(f"[DEBUG] grid_spheres_3d: center=({cx:.3f},{cy:.3f},{cz:.3f})")

                # 球体をZ方向のレベルで分割（Z=0から上方向）
                for level in range(levels):
                    # Z=0から球体上部まで
                    z_offset = (level / levels) * 2 * r - r  # -r から +r
                    z_pos = max(0, cz + z_offset)  # Z=0未満は0にクランプ

                    # 切断面での円の半径（XY平面）
                    if abs(z_offset) <= r:
                        circle_r = math.sqrt(r * r - z_offset * z_offset)
                        if circle_r > 0.5:  # 最小半径
                            steps = max(6, int(circle_r * 4))

                            # 円の開始点へ移動
                            if level == 0:
                                g.exec(f"G0 X{cx + circle_r:.3f} Y{cy:.3f} Z0")  # 最初は必ずZ=0
                            else:
                                g.exec(f"G0 X{cx + circle_r:.3f} Y{cy:.3f} Z{z_pos:.3f}")

                            # XY平面で円を描画
                            for step in range(steps + 1):
                                angle = 2 * math.pi * step / steps
                                x = cx + circle_r * math.cos(angle)
                                y = cy + circle_r * math.sin(angle)

                                if level == 0:
                                    g.exec(f"G1 X{x:.3f} Y{y:.3f} Z0")  # 最初のレベルはZ=0
                                else:
                                    g.exec(f"G1 X{x:.3f} Y{y:.3f} Z{z_pos:.3f}")

                total_spheres += 1

    print(f"合計 {total_spheres} 個の球体を描画しました")
    return f"3Dグリッド球体パターンを実行しました (cell={cell}mm, sphere_d={sphere_d}mm)"


# ========= G-code/STEPファイル読み込み =========
def load_gcode_or_stp(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".gcode", ".nc", ".tap"]:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "gcode", lines
    elif ext in [".stp", ".step"]:
        try:
            from OCC.Core.IFSelect import IFSelect_RetDone
            from OCC.Core.STEPControl import STEPControl_Reader

            reader = STEPControl_Reader()
            status = reader.ReadFile(file_path)
            if status != IFSelect_RetDone:
                raise Exception("STEPファイルの読み込みに失敗しました")
            reader.TransferRoots()
            shape = reader.Shape()
            return "stp", shape
        except ModuleNotFoundError:
            print(
                "STEP処理には pythonocc-core が必要です。"
                " `pip install -e \".[step]\"` で導入してください。"
            )
            return None, None
        except Exception as e:
            print(f"STEPファイル読み込みエラー: {e}")
            return None, None
    else:
        print("未対応ファイル形式: ", ext)
        return None, None


def process_step_file_simple(g, file_path, origin, resolution):
    """
    STEPファイルの簡易処理（球体形状を近似）
    実際の実装では pythonocc-core を使用
    """
    ox, oy, oz = origin
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # STEPファイルから球体情報を抽出（改良版パーサー）
    spheres = []
    lines = content.split("\n")

    # まず球体表面を検出
    sphere_surfaces = {}
    for line in lines:
        if "SPHERICAL_SURFACE" in line:
            parts = line.split("=")[0].strip("#")
            if parts.isdigit():
                entity_id = int(parts)
                # 半径を抽出
                if "," in line:
                    try:
                        radius_part = line.split(",")[-1].replace(")", "").replace(";", "").strip()
                        radius = float(radius_part)
                        sphere_surfaces[entity_id] = radius
                    except (ValueError, IndexError):
                        sphere_surfaces[entity_id] = 10.0  # デフォルト半径

    # 座標点を検出
    points = {}
    for line in lines:
        if "CARTESIAN_POINT" in line:
            parts = line.split("=")[0].strip("#")
            if parts.isdigit():
                entity_id = int(parts)
                if "(" in line and ")" in line:
                    coords_str = line[line.find("(") + 1 : line.rfind(")")]
                    coord_parts = [p.strip() for p in coords_str.split(",")]
                    if len(coord_parts) >= 3:
                        try:
                            # 最後の3つの数値を座標として取得
                            coords = []
                            for part in coord_parts[-3:]:
                                if part.replace(".", "").replace("-", "").isdigit():
                                    coords.append(float(part))
                            if len(coords) == 3:
                                points[entity_id] = coords
                        except ValueError:
                            continue

    # デフォルトの球体を追加（パースに失敗した場合）
    if not sphere_surfaces:
        print("STEPファイルの解析に失敗。デフォルト球体を使用")
        spheres = [
            {"center": (0, 0, 0), "radius": 10.0},
            {"center": (20, 0, 0), "radius": 7.0},
            {"center": (0, 20, 10), "radius": 3.0},
        ]
    else:
        # 検出した球体情報を統合
        for surface_id, radius in sphere_surfaces.items():
            # 対応する中心点を検索（近い番号のポイントを使用）
            center = (0, 0, 0)  # デフォルト
            for point_id, coords in points.items():
                if abs(point_id - surface_id) <= 2:  # 近い番号のポイント
                    center = tuple(coords)
                    break
            spheres.append({"center": center, "radius": radius})

    print(f"STEPファイルから {len(spheres)} 個の球体を検出")

    # 各球体を近似的に描画
    for i, sphere in enumerate(spheres):
        cx, cy, cz = sphere["center"]
        r = sphere["radius"]
        cx += ox
        cy += oy
        cz += oz

        print(f"球体 {i+1}: 中心=({cx:.1f},{cy:.1f},{cz:.1f}), 半径={r:.1f}")

        # 球体をXY平面（Z軸方向）で複数レベルに分割
        levels = max(3, int(r / resolution))

        # Z=0から開始し、球体の下半分から上半分へ
        for level in range(levels + 1):
            # Z座標での水平切断面（Z=0から開始）
            z_offset = (level / levels) * 2 * r - r  # -r から +r
            z_pos = cz + z_offset

            # 切断面での円の半径（XY平面）
            if abs(z_offset) <= r:
                circle_r = math.sqrt(r * r - z_offset * z_offset)
                if circle_r > 0.1:  # 最小半径制限
                    # XY平面で円を描画
                    steps = max(8, int(circle_r * 6))

                    # Z=0から開始する場合の特別処理
                    if level == 0:
                        print(f"  Z=0レベルから開始: 半径={circle_r:.2f}mm")
                        g.exec(f"G0 X{cx + circle_r:.3f} Y{cy:.3f} Z0")  # Z=0から開始
                    else:
                        g.exec(f"G0 X{cx + circle_r:.3f} Y{cy:.3f} Z{z_pos:.3f}")

                    for step in range(steps + 1):
                        angle = 2 * math.pi * step / steps
                        x = cx + circle_r * math.cos(angle)
                        y = cy + circle_r * math.sin(angle)

                        # 最初のレベル（Z=0）は常にZ=0で描画
                        if level == 0:
                            g.exec(f"G1 X{x:.3f} Y{y:.3f} Z0")
                        else:
                            g.exec(f"G1 X{x:.3f} Y{y:.3f} Z{z_pos:.3f}")


def select_file_with_dialog(env: EnvironmentAdapter, title, filetypes):
    """GUIでファイルを選択（クロスプラットフォーム対応）"""
    initial_dir = str(ROOT_DIR / "drawing_data")
    if not os.path.exists(initial_dir):
        initial_dir = env.normalize_path(".")
    return env.select_file_dialog(title, filetypes, initialdir=initial_dir)


def select_and_execute_file(env: EnvironmentAdapter):
    """ファイルダイアログでG-codeまたはSTEPファイルを選択して実行"""
    info = env.get_platform_info()
    platform_name = {
        "windows": "Windows",
        "darwin": "macOS",
        "linux": "Linux",
    }.get(info["system"], info["system"].title())

    print(f"\n=== XYZ Runner (3D) - {platform_name} ===")
    print("G-codeまたはSTEPファイルを選択してください...")

    file_path = select_file_with_dialog(
        env,
        "G-codeまたはSTEPファイルを選択してください",
        [
            ("G-code files", "*.gcode *.nc *.tap"),
            ("STEP files", "*.stp *.step"),
            ("All supported", "*.gcode *.nc *.tap *.stp *.step"),
            ("All files", "*.*"),
        ],
    )

    if not file_path or not os.path.exists(file_path):
        print("ファイルが選択されませんでした。")
        return None, None

    # 拡張子から判定
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".gcode", ".nc", ".tap"]:
        return file_path, "gcode"
    elif ext in [".stp", ".step"]:
        return file_path, "stp"
    else:
        print(f"サポートされていないファイル形式です: {ext}")
        return None, None


# ========= メイン =========
def main():
    ap = argparse.ArgumentParser(description="Config-driven XYZ runner (3D)")
    ap.add_argument("--config", help="YAML config path")
    ap.add_argument("--driver", choices=["sim", "chuo"])
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--no-animate", action="store_true", help="アニメーション無効化")
    ap.add_argument("--debug", action="store_true", help="[DEBUG]出力を有効化")
    ap.add_argument("--file", help="G-codeまたはSTEPファイルパス")
    args = ap.parse_args()
    # logging はファイル先頭でインポート済み
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
    app = XYZRunnerApp(args)
    app.run(file_override=args.file)


if __name__ == "__main__":
    main()
