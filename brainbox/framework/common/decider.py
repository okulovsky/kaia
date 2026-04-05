from uuid import uuid4
from .api_callback import ApiCallback
from .loc import Loc
from pathlib import Path
from dataclasses import dataclass, field

class DeciderContext:
    def __init__(self):
        self._api_callback : ApiCallback|None = None
        self._current_job_id: str|None = None
        self._cache_folder: Path|None = None

    @property
    def api_callback(self) -> ApiCallback:
        if self._api_callback is None:
            return ApiCallback()
        return self._api_callback

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

    def get_name(self):
        return type(self).__name__

