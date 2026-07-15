from typing import *
from ...common import ApiCallback, BrainBoxLocations
from .resource_folder import ResourceFolder
from ...deployment import Machine, LocalExecutor, IExecutor
from pathlib import Path


TSettings = TypeVar("TSettings")


class ControllerContext(Generic[TSettings]):
    def __init__(self, name: str, settings: TSettings):
        self._name = name
        self.settings = settings
        self._resource_folder_root : Path | None = None
        self._api_callback: ApiCallback | None = None
        self._machine: Machine|None = None
        self._executor: IExecutor | None = None
        self._instance_registry = None

    @property
    def resource_folder_root(self) -> Path:
        if self._resource_folder_root is None:
            return BrainBoxLocations.default_resources_folder()
        return self._resource_folder_root

    @property
    def resource_folder(self) -> ResourceFolder:
        return ResourceFolder(self.resource_folder_root/self._name)

    @property
    def api_callback(self):
        if self._api_callback is None:
            return ApiCallback()
        return self._api_callback


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

    @property
    def instance_registry(self) -> 'InstancesRegistry':
        if self._instance_registry is None:
            from .instances_registry import InstancesRegistry
            self._instance_registry = InstancesRegistry()
        return self._instance_registry


