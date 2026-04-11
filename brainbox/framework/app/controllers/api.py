from brainbox.framework.controllers.architecture.controller_registry import ControllerRegistry, ControllerLike
from foundation_kaia.marshalling_2.marshalling.server.api_call import ApiCall
from .dto import ControllersSetup
from .interface import IControllersService
from .side_process import SideProcessApi


class InternalControllersApi(IControllersService):
    def __init__(self, base_url: str) -> None:
        ApiCall.define_endpoints(self, base_url, IControllersService)


class ControllersApi:
    def __init__(self, base_url):
        self._internal = InternalControllersApi(base_url)
        self.install = SideProcessApi(base_url, 'controllers-service/install')
        self.self_test = SideProcessApi(base_url, 'controllers-service/self-test')

    def _name(self, decider: str | ControllerLike) -> str:
        return ControllerRegistry.to_controller_name(decider)

    def status(self):
        return self._internal.status()

    def uninstall(self, decider: str | ControllerLike, purge: bool | None = None) -> None:
        return self._internal.uninstall(self._name(decider), purge)

    def run(self, decider: str | ControllerLike, parameter: str | None = None) -> str:
        return self._internal.run(self._name(decider), parameter)

    def stop(self, decider: str | ControllerLike, instance_id: str) -> None:
        return self._internal.stop(self._name(decider), instance_id)

    def delete_self_test(self, decider: str | ControllerLike) -> None:
        return self._internal.delete_self_test(self._name(decider))

    def self_test_report(self, decider: str|ControllerLike) -> str:
        return self._internal.self_test_report(self._name(decider))

    def setup(self, setup: ControllersSetup):
        return self._internal.setup(setup)



