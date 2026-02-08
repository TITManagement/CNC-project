"""
ランタイム構成要素: 設定ロード。
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import yaml


class ConfigLoader:
    """YAML 設定の読み込みと既定値適用を担う。"""

    def __init__(self, default_factory: Optional[Callable[[Optional[str]], dict]] = None):
        self._default_factory = default_factory

    def load(self, path: Optional[str], *, driver_override: Optional[str] = None) -> dict:
        config: Optional[dict] = None
        if path:
            cfg_path = Path(path)
            if not cfg_path.exists():
                raise FileNotFoundError(f"設定ファイルが見つかりません: {path}")
            with cfg_path.open("r", encoding="utf-8") as fh:
                config = yaml.safe_load(fh) or {}
        elif self._default_factory is not None:
            config = self._default_factory(driver_override)

        if config is None:
            config = {}

        if driver_override:
            config["driver"] = driver_override

        return config
