"""
Compatibility wrapper for the canonical CncDriver interface.

`CncDriver` の正本は `cnc_drivers.driver_base` に集約する。
本モジュールは既存 import パス維持のために再エクスポートのみ行う。
"""

from __future__ import annotations

from cnc_drivers.driver_base import CncDriver

__all__ = ["CncDriver"]
