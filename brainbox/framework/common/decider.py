from uuid import uuid4
from .logger import Logger
from .loc import Loc
from pathlib import Path
from dataclasses import dataclass, field

class DeciderContext:
    def __init__(self):
        self._logger : Logger|None = None
        self._current_job_id: str|None = None
        self._cache_folder: Path|None = None

    @property
    def logger(self) -> Logger:
        if self._logger is None:
            return Logger()
        return self._logger

    @property
    def current_job_id(self) -> str:
        if self._current_job_id is None:
            return str(uuid4())
        return self._current_job_id

    @property
    def cache_folder(self) -> Path:
        if self._cache_folder is None:
            return Loc.cache_folder
        return self._cache_folder


class IDecider:
    @property
    def context(self) -> DeciderContext:
        if not hasattr(self, '_context'):
            self._context = DeciderContext()
        return self._context

    @context.setter
    def context(self, value: DeciderContext):
        self.context = value

    @property
    def cache_folder(self) -> Path:
        return self.context.cache_folder

    @property
    def current_job_id(self) -> str:
        return self.context.current_job_id

    @classmethod
    def get_ordering_arguments_sequence(cls) -> tuple[str,...]|None:
        return None


class ISelfManagingDecider(IDecider):
    def warmup(self, parameter: str|None):
        pass

    def cooldown(self):
        pass

