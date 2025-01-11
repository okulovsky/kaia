from dataclasses import dataclass
from ..controller import InstallationStatus
from .logging import Log


@dataclass
class ControllerServiceStatus:
    InstallationStatus = InstallationStatus

    @dataclass
    class Instance:
        instance_id: str
        parameter: str | None
        address: str | None

    @dataclass
    class Controller:
        name: str
        installation_status: InstallationStatus
        has_self_test_report: bool = False
        has_errors_in_self_test_report: bool = False
        instances: tuple['ControllerServiceStatus.Instance', ...] = ()


    containers: list['ControllerServiceStatus.Controller']
    currently_installing_container: str|None




@dataclass
class InstallationReport:
    name: str
    log: Log
    error: str|None = None


@dataclass
class ControllerInstanceSetup:
    decider: type|str
    parameter: str|None = None
    loaded_model: str|None = None


@dataclass
class ControllersSetup:
    controllers: tuple[ControllerInstanceSetup,...]

    Instance = ControllerInstanceSetup
