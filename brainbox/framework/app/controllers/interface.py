from foundation_kaia.marshalling import service, endpoint
from .dto import (ControllersStatus, InstallationReport, SelfTestResult, ControllersSetup)


@service
class IControllersService:
    @endpoint(method='GET')
    def status(self) -> ControllersStatus:
        ...

    @endpoint(method='POST')
    def install(self, decider: str, join: bool | None = None) -> InstallationReport | None:
        ...

    @endpoint(method='POST')
    def uninstall(self, decider: str, purge: bool | None = None) -> None:
        ...

    @endpoint(method='POST')
    def run(self, decider: str, parameter: str | None = None) -> str:
        ...

    @endpoint(method='POST')
    def stop(self, decider: str, instance_id: str) -> None:
        ...

    @endpoint(method='POST')
    def self_test(self, decider: str) -> SelfTestResult:
        ...

    @endpoint(method='GET')
    def self_test_report(self, decider: str) -> str:
        ...


    @endpoint(method='POST')
    def delete_self_test(self, decider: str) -> None:
        ...

    @endpoint(method='POST')
    def setup(self, setup: ControllersSetup) -> None:
        ...

