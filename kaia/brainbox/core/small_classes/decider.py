from typing import *
from abc import ABC, abstractmethod
from .progress_reporter import IProgressReporter, EmptyProgressReporter
from pathlib import Path
from kaia.infra import Loc
import os


class DeciderForDebugging:
    def __init__(self, decider: 'IDecider', parameters):
        self.decider = decider
        self.parameters = parameters


    def __enter__(self):
        self.decider.warmup(self.parameters)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.decider.cooldown(self.parameters)


class IDecider:
    @property
    def progress_reporter(self) -> IProgressReporter:
        if hasattr(self, '_progress_reporter'):
            if self._progress_reporter is not None:
                return self._progress_reporter
            else:
                return EmptyProgressReporter()
        else:
            return EmptyProgressReporter()

    @property
    def file_cache(self) -> Path:
        if hasattr(self, '_file_cache'):
            return self._file_cache
        else:
            path = Loc.temp_folder/'deciders_output'
            os.makedirs(path, exist_ok=True)
            return path

    def _setup_environment(self, file_cache: Path,  progress_reporter: IProgressReporter):
        self._progress_reporter = progress_reporter
        self._file_cache = file_cache

    @abstractmethod
    def warmup(self, parameters: str):
        pass

    @abstractmethod
    def cooldown(self, parameters: str):
        pass

    def debug(self, parameters: Optional[str] = None):
        return DeciderForDebugging(self, parameters)
