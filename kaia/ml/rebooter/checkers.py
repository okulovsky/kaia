from typing import *
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
import os


class IRestartChecker(ABC):
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def should_restart(self) -> Optional[str]:
        pass


class FileRestartChecker(IRestartChecker):
    def __init__(self,
                 file_to_monitor: Path,
                 allowed_pause_in_seconds: int
                 ):
        self.file_to_monitor = file_to_monitor
        self.allowed_pause_in_seconds = allowed_pause_in_seconds

    def reset(self):
        self.restart_time = datetime.now()

    def should_restart(self) -> Optional[str]:
        stat = os.stat(self.file_to_monitor)
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        now = datetime.now()
        if (now - self.restart_time).total_seconds() < self.allowed_pause_in_seconds:
            return None
        if (now - last_modified).total_seconds() > self.allowed_pause_in_seconds:
            return 'file_not_updated'
        return None
