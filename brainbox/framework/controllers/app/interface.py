from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from ..controller import InstallationStatus, IController
from .logging import Log
import traceback

@dataclass
class ControllerInstanceStatus:
    instance_id: str
    parameter: str|None
    address: str|None

@dataclass
class ControllerStatus:
    name: str
    installation_status: InstallationStatus
    has_self_test_report: bool = False
    has_errors_in_self_test_report: bool = False
    instances: tuple[ControllerInstanceStatus,...] = ()


@dataclass
class ControllerServicesStatus:
    containers: list[ControllerStatus]
    currently_installing_container: str|None


@dataclass
class InstallationReport:
    name: str
    log: Log
    error: str|None = None



class IControllerService(ABC):
    @abstractmethod
    def status(self) -> ControllerServicesStatus:
        pass

    @abstractmethod
    def install(self, decider: str|type, join: bool = True) -> InstallationReport|None:
        pass


    @abstractmethod
    def uninstall(self, decider: str|type, purge: bool = False):
        pass

    @abstractmethod
    def run(self, decider: str|type, parameter: str|None = None) -> str:
        pass

    @abstractmethod
    def stop(self, decider: str|type, instance_id: str|None = None):
        pass

    @abstractmethod
    def join_installation(self) -> InstallationReport:
        pass

    @abstractmethod
    def installation_report(self) -> InstallationReport:
        pass

    @abstractmethod
    def self_test(self, decider: str|type):
        pass

    @abstractmethod
    def delete_self_test(self, decider: str|type):
        pass

    @abstractmethod
    def list_resources(self, decider: str|type, path: str):
        pass

    @abstractmethod
    def delete_resource(self, decider: str|type, path: str, ignore_errors: bool = False):
        pass



