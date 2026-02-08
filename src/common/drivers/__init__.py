"""
Compatibility shims for XYZ runner.

`ChuoDriver` はここでは実装していません。実機を使う場合は
適切なドライバ実装に差し替えてください。
"""
from .driver_base import CncDriver


class ChuoDriver(CncDriver):
    """実機ドライバのダミー実装（未実装）。"""

    def set_units_mm(self) -> None:
        raise NotImplementedError("ChuoDriver is not implemented in this package.")

    def set_units_inch(self) -> None:
        raise NotImplementedError("ChuoDriver is not implemented in this package.")

    def home(self) -> None:
        raise NotImplementedError("ChuoDriver is not implemented in this package.")

    def move_abs(self, *, feed=None, rapid=False, **axes):
        raise NotImplementedError("ChuoDriver is not implemented in this package.")


__all__ = ["CncDriver", "ChuoDriver"]
