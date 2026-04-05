from dataclasses import dataclass, field
from datetime import datetime
from ...controllers import ControllerRegistry, ControllerLike


@dataclass
class LogItem:
    timestamp: datetime
    data: str


@dataclass
class InstallationReport:
    name: str
    log: list[LogItem]
    error: str | None = None


@dataclass
class ControllerInstance:
    instance_id: str
    parameter: str | None
    address: str | None


@dataclass
class ControllerStatus:
    name: str
    installed: bool
    dockerless: bool
    size: str | None
    has_self_test_report: bool
    has_errors_in_self_test_report: bool
    instances: list[ControllerInstance]


@dataclass
class ControllersStatus:
    controllers: list[ControllerStatus]
    currently_installing: str | None


@dataclass
class SelfTestSectionResult:
    caption: str | None
    comment: str | None
    item_count: int


@dataclass
class SelfTestResult:
    name: str
    sections: list[str]
    error: str|None = None

@dataclass
class ControllersSetup:
    simple_deciders: list[str] = field(default_factory=list)
    deciders_with_model: dict[str, str] = field(default_factory=dict)
    deciders_with_parameters: dict[str, str] = field(default_factory=dict)

    def up(self, decider: ControllerLike, *, model: str|None = None, parameter: str|None = None) -> 'ControllersSetup':
        name = ControllerRegistry.to_controller_name(decider)
        if model is not None:
            self.deciders_with_model[name] = model
        elif parameter is not None:
            self.deciders_with_parameters[name] = parameter
        else:
            self.simple_deciders.append(name)
        return self
