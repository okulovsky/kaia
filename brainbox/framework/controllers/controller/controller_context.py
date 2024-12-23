from typing import *
from ...common import Logger, Loc
from .resource_folder import ResourceFolder
from .mounting_prefix import MountingPrefix
from ...deployment import Machine, LocalExecutor, IExecutor
from pathlib import Path


TSettings = TypeVar("TSettings")


class ControllerContext(Generic[TSettings]):
    def __init__(self, name: str, settings: TSettings):
        self._name = name
        self.settings = settings
        self._resource_folder_root : Path | None = None
        self._logger: Logger | None = None
        self._mounting_prefix: MountingPrefix | None = None
        self._machine: Machine|None = None
        self._executor: IExecutor | None = None

    @property
    def resource_folder_root(self) -> Path:
        if self._resource_folder_root is None:
            return Loc.resources_folder
        return self._resource_folder_root

    @property
    def resource_folder(self) -> ResourceFolder:
        return ResourceFolder(self.resource_folder_root/self._name)

    @property
    def logger(self):
        if self._logger is None:
            return Logger()
        return self._logger

    @property
    def mounting_prefix(self) -> MountingPrefix:
        if self._mounting_prefix is None:
            return MountingPrefix()
        return self._mounting_prefix

    @property
    def machine(self) -> Machine:
        if self._machine is None:
            return Machine.local()
        return self._machine

    @property
    def executor(self) -> IExecutor:
        if self._executor is None:
            return LocalExecutor()
        return self._executor


