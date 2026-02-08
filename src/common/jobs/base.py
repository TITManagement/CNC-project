"""
ジョブ実行の共通インターフェースとファクトリ。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Mapping, Optional, Protocol


class Job(ABC):
    """ジョブ設定を保持し、実行手順を定義する基底クラス。"""

    def __init__(self, config: Mapping):
        self.config = config

    @abstractmethod
    def execute(self, *, gcode, context: Optional[Mapping] = None) -> None:
        """ジョブを実行する。"""


class JobCreator(Protocol):
    def __call__(self, config: Mapping) -> Job: ...


class JobFactory:
    """ジョブタイプに応じて `Job` インスタンスを生成する。"""

    def __init__(self) -> None:
        self._registry: Dict[str, JobCreator] = {}

    def register(self, job_type: str, creator: JobCreator) -> None:
        self._registry[job_type] = creator

    def create(self, job_config: Mapping) -> Optional[Job]:
        job_type = job_config.get("type")
        if not job_type:
            print("ジョブタイプが指定されていません。スキップします。")
            return None
        creator = self._registry.get(job_type)
        if creator is None:
            print(f"未対応ジョブタイプ: {job_type}")
            return None
        return creator(job_config)
