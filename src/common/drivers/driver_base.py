"""
Minimal CNC driver base class for XYZ runner compatibility.

このプロジェクトでは3Dランナーはシミュレーションが主用途のため、
実機ドライバは未実装。必要に応じて適宜置き換えてください。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class CncDriver(ABC):
    axes: tuple[str, ...] = ()

    @abstractmethod
    def set_units_mm(self) -> None:
        ...

    @abstractmethod
    def set_units_inch(self) -> None:
        ...

    @abstractmethod
    def home(self) -> None:
        ...

    @abstractmethod
    def move_abs(self, *, feed: Optional[float] = None, rapid: bool = False, **axes: float) -> None:
        ...

    def close(self) -> None:
        """リソース解放が必要な場合は実装側でオーバーライド。"""
        pass

