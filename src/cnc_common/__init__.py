"""Compatibility shims for legacy `cnc_common` imports.

Actual implementations live under the `common` package. These modules simply
re-export the same symbols so existing code importing `cnc_common.*` continues
to work.
"""
from importlib import import_module

gcode = import_module("common.gcode")
jobs = import_module("common.jobs")
platform = import_module("common.platform")
runtime = import_module("common.runtime")

__all__ = ["gcode", "jobs", "platform", "runtime"]
