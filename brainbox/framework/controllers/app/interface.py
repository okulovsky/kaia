from abc import ABC, abstractmethod
from .dto import *


class IControllerService(ABC):
    @abstractmethod
    def status(self) -> ControllerServiceStatus:
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
    def list_resources(self, decider: str|type, path: str) -> list[str]:
        pass

    @abstractmethod
    def delete_resource(self, decider: str|type, path: str, ignore_errors: bool = False):
        pass

    @abstractmethod
    def setup(self, setup: ControllersSetup):
        pass

    @abstractmethod
    def download_models(self, decider: str|type, models: list):
        pass