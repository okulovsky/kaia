from dataclasses import dataclass
from datetime import datetime


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
    base_url: str | None


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
class SelfTestCaseDocumentation:
    title: str | None
    method: str
    arguments: dict


@dataclass
class MethodExamples:
    method_name: str
    self_test_cases: list[SelfTestCaseDocumentation]
    is_file: list[str]
    result_is_file: bool


@dataclass
class ControllerExamples:
    name: str
    docstring: str | None
    methods: list[MethodExamples]


