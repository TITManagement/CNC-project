"""
可視化制御ユーティリティ。
"""

from __future__ import annotations

import os
from typing import Optional


class VisualizationController:
    """軌跡表示の可否やタイトル組み立てを担当する。"""

    def __init__(
        self,
        driver,
        *,
        default_title: str = "Simulation",
        done_message: Optional[str] = None,
        skip_message: Optional[str] = None,
    ) -> None:
        self._driver = driver
        self._default_title = default_title
        self._done_message = done_message
        self._skip_message = skip_message

    def show(
        self,
        *,
        cfg_visual: Optional[dict] = None,
        force_show: bool = False,
        disable_animate: bool = False,
        selected_file: Optional[str] = None,
    ) -> bool:
        visual = cfg_visual or {}
        show_flag = force_show or bool(visual.get("show", False))
        if not show_flag:
            if self._skip_message:
                print(self._skip_message)
            return False

        animate = not disable_animate and bool(visual.get("animate", True))
        fps = int(visual.get("fps", 30))
        title = visual.get("title", self._default_title)
        if selected_file:
            title = f"{title} - {os.path.basename(selected_file)}"

        self._driver.animate_tracks(animate=animate, fps=fps, title=title)

        if self._done_message:
            print(self._done_message)

        return True
