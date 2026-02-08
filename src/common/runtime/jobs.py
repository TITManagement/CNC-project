"""
ジョブディスパッチャ。
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional

from cnc_drivers.job_base import JobFactory


class JobDispatcher:
    """ジョブ設定を `JobFactory` 経由で実行する。"""

    def __init__(self, factory: JobFactory):
        self._factory = factory

    def dispatch_job(
        self,
        job_cfg: Mapping,
        *,
        gcode,
        context: Optional[Mapping] = None,
    ) -> None:
        job = self._factory.create(job_cfg)
        if job is None:
            return
        job.execute(gcode=gcode, context=context)

    def dispatch_jobs(
        self,
        jobs: Iterable[Mapping],
        *,
        gcode,
        context: Optional[Mapping] = None,
    ) -> None:
        for job_cfg in jobs or []:
            self.dispatch_job(job_cfg, gcode=gcode, context=context)
