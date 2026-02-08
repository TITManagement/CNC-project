"""
G-code インタープリタの共通基盤。

XY/XYZ ランナー双方の重複を吸収し、各軸固有の処理のみ派生クラスで
扱えるようにする。基本的なモーダル状態の更新（単位・座標モード・
送り速度）と直線移動はここで担う。
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

__all__ = [
    "BaseModalState",
    "ModalState2D",
    "ModalState3D",
    "BaseGCodeInterpreter",
    "LinearGCodeInterpreter",
]


@dataclass
class BaseModalState:
    """G-code モーダル情報の共通フィールド。"""

    units_mm: bool = True
    absolute: bool = True
    feed: float = 1200.0


@dataclass
class ModalState2D(BaseModalState):
    """XY 走査用のモーダル状態。"""

    xpos: float = 0.0
    ypos: float = 0.0


@dataclass
class ModalState3D(BaseModalState):
    """XYZ 走査用のモーダル状態。"""

    xpos: float = 0.0
    ypos: float = 0.0
    zpos: float = 0.0


class BaseGCodeInterpreter(ABC):
    """
    G-code 行を解釈してドライバへ指示を送る基底クラス。

    - コメント除去
    - モーダルコマンド（単位・座標モード・送り速度）の適用
    - ホーミングコマンドの処理
    """

    modal_state_cls = BaseModalState
    motion_g_codes: Tuple[int, ...] = (0, 1)

    def __init__(self, driver):
        self.drv = driver
        self.m = self._create_modal_state()

    def _create_modal_state(self) -> BaseModalState:
        return self.modal_state_cls()

    def exec(self, line: str) -> None:
        logging.debug("[GCode] exec: %s", line)
        line = self._strip_comment(line).strip()
        if not line:
            return
        if line.startswith("$H"):
            if hasattr(self.drv, "home"):
                self.drv.home()
            return

        words = re.findall(r"[A-Za-z][+\-0-9\.]*", line)
        if not words:
            return

        self._apply_modal(words)
        self._update_feed(words)

        if self._contains_motion(words):
            self._handle_motion(words)

    def _apply_modal(self, words: Iterable[str]) -> None:
        for w in words:
            code, value = w[0].upper(), w[1:]
            if code != "G":
                continue
            try:
                g = float(value)
            except ValueError:
                continue
            if g == 20:
                self.m.units_mm = False
                if hasattr(self.drv, "set_units_inch"):
                    self.drv.set_units_inch()
            elif g == 21:
                self.m.units_mm = True
                if hasattr(self.drv, "set_units_mm"):
                    self.drv.set_units_mm()
            elif g == 90:
                self.m.absolute = True
            elif g == 91:
                self.m.absolute = False

    def _update_feed(self, words: Iterable[str]) -> None:
        for w in words:
            if w[0].upper() == "F":
                try:
                    self.m.feed = float(w[1:])
                except ValueError:
                    continue

    def _contains_motion(self, words: Iterable[str]) -> bool:
        for w in words:
            if w[0].upper() != "G":
                continue
            try:
                g = int(float(w[1:]))
            except ValueError:
                continue
            if g in self.motion_g_codes:
                return True
        return False

    @abstractmethod
    def _handle_motion(self, words: Iterable[str]) -> None:
        """派生クラスでモーションコマンドを処理する。"""

    def _unit_to_mm(self, value: float) -> float:
        return value if self.m.units_mm else value * 25.4

    @staticmethod
    def _strip_comment(source: str) -> str:
        source = re.sub(r"\(.*?\)", "", source)
        return source.split(";", 1)[0]


class LinearGCodeInterpreter(BaseGCodeInterpreter):
    """
    G0/G1 など直線移動に対応した G-code インタープリタ。

    `linear_axes` に列挙した軸についてモーダル座標を保持し、移動指示を
    ドライバへ送る。派生クラスでは円弧など追加モーションが必要な場合、
    `_handle_extended_motion` を上書きする。
    """

    linear_axes: Tuple[str, ...] = ()
    extra_params: Tuple[str, ...] = ()
    motion_g_codes: Tuple[int, ...] = (0, 1)

    def _handle_motion(self, words: Iterable[str]) -> None:
        gcode = None
        params: Dict[str, float] = {}

        for w in words:
            code, value = w[0].upper(), w[1:]
            if code == "G":
                try:
                    gcode = int(float(value))
                except ValueError:
                    continue
            elif code in self.linear_axes or code in self.extra_params or code == "F":
                try:
                    params[code] = float(value)
                except ValueError:
                    continue

        if gcode in (0, 1):
            self._handle_linear_move(gcode, params)
            return

        self._handle_extended_motion(gcode, params, words)

    def _handle_linear_move(self, gcode: int, params: Dict[str, float]) -> None:
        targets: Dict[str, float] = {}
        for axis in self.linear_axes:
            attr = f"{axis.lower()}pos"
            current = getattr(self.m, attr, 0.0)
            if axis in params:
                raw = params[axis]
                delta = self._unit_to_mm(raw)
                target = delta if self.m.absolute else current + delta
            else:
                target = current
            targets[axis] = target

        feed = params["F"] if "F" in params else None
        feed_value = self._unit_to_mm(feed) if feed is not None else getattr(self.m, "feed", None)

        driver_kwargs = {axis.lower(): targets[axis] for axis in self.linear_axes}
        self.drv.move_abs(feed=feed_value, rapid=(gcode == 0), **driver_kwargs)

        for axis, value in targets.items():
            setattr(self.m, f"{axis.lower()}pos", value)

    def _handle_extended_motion(
        self, gcode: int | None, params: Dict[str, float], words: Iterable[str]
    ) -> None:
        if gcode is None:
            return
        raise NotImplementedError(f"G{gcode} は未対応です")
