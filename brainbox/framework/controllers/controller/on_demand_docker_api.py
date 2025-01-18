from ...deployment import Deployment
from ...common import IDecider
from typing import Generic, TypeVar
from .run_configuration import RunConfiguration


TSettings = TypeVar('TSettings')
TController = TypeVar('TController')


class MonitorFunctionWrapper:
    def __init__(self, monitor_function):
        self.monitor_function = monitor_function

    def __call__(self, line):
        print(line)
        if self.monitor_function is not None:
            self.monitor_function(line)

class OnDemandDockerApi(IDecider, Generic[TSettings, TController]):
    @property
    def controller(self) -> TController:
        return self._controller

    @controller.setter
    def controller(self, controller: TController):
        self._controller = controller

    def run_container(self, configuration: RunConfiguration, monitor_function = None):
        from .on_demand_docker_controller import OnDemandDockerController
        controller: OnDemandDockerController = self.controller
        controller.get_deployment().stop().remove()
        controller.run_with_configuration(configuration, MonitorFunctionWrapper(monitor_function))



