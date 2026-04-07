from typing import Iterable
from brainbox.framework.controllers.architecture.controller_registry import ControllerRegistry, ControllerLike
from brainbox.framework import Loc, Locator
from foundation_kaia.marshalling_2.marshalling.server import Server, ServiceComponent, TestApi
from foundation_kaia.marshalling_2.marshalling.server.api_call import ApiCall
from pathlib import Path
from .dto import InstallationReport, SelfTestResult, ControllersSetup
from .interface import IControllersService
from .service import ControllersService


class InternalControllersApi(IControllersService):
    def __init__(self, base_url: str) -> None:
        ApiCall.define_endpoints(self, base_url, IControllersService)


class ControllersApi:
    def __init__(self, internal_api: IControllersService):
        self._internal = internal_api

    def _name(self, decider: str | ControllerLike) -> str:
        return ControllerRegistry.to_controller_name(decider)

    def status(self):
        return self._internal.status()

    def install(self, decider: str | ControllerLike, join: bool | None = None) -> InstallationReport | None:
        return self._internal.install(self._name(decider), join)

    def uninstall(self, decider: str | ControllerLike, purge: bool | None = None) -> None:
        return self._internal.uninstall(self._name(decider), purge)

    def run(self, decider: str | ControllerLike, parameter: str | None = None) -> str:
        return self._internal.run(self._name(decider), parameter)

    def stop(self, decider: str | ControllerLike, instance_id: str) -> None:
        return self._internal.stop(self._name(decider), instance_id)

    def join_installation(self) -> InstallationReport:
        return self._internal.join_installation()

    def installation_report(self) -> InstallationReport:
        return self._internal.installation_report()

    def self_test(self, decider: str | ControllerLike) -> SelfTestResult:
        return self._internal.self_test(self._name(decider))

    def delete_self_test(self, decider: str | ControllerLike) -> None:
        return self._internal.delete_self_test(self._name(decider))

    def setup(self, setup: ControllersSetup):
        return self._internal.setup(setup)



    @staticmethod
    def test(services: Iterable[ControllerLike] | None = None,
             custom_folder: Path | None = None,
             port: int = 18192,
             ) -> 'TestApi[ControllersApi]':
        loc = Locator(custom_folder) if custom_folder is not None else Loc
        registry = ControllerRegistry.discover_or_create(services)
        registry.locator = loc
        return TestApi(lambda u: ControllersApi(InternalControllersApi(u)), Server(port, ServiceComponent(ControllersService(registry))))

