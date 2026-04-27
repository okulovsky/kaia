from ...logging import Logger, ILogItem
from dataclasses import dataclass
from typing import Any

@dataclass
class ProgressItem(ILogItem):
    progress: float

    def to_string(self) -> str:
        return f'PROGRESS: {self.progress}'


class BrainboxLogger(Logger):
    def progress(self, value: float):
        self.log(ProgressItem(value))


logger = BrainboxLogger()


