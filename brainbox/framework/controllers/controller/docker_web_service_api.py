from typing import TypeVar, Generic
from .docker_web_service_controller import DockerWebServiceController
from ...common import ApiUtils, IDecider

TSettings = TypeVar('TSettings')
TController = TypeVar('TController')

class DockerWebServiceApi(IDecider, Generic[TSettings, TController]):
    def __init__(self, address: str|None, container_parameter: str|None = None):
        if address is not None:
            ApiUtils.check_address(address)
        self._custom_address = address
        self._controller: DockerWebServiceController|None = None
        self._container_parameter: container_parameter



    @property
    def controller(self) -> TController:
        return self._controller

    @controller.setter
    def controller(self, controller: TController):
        self._controller = controller

    @property
    def address(self) -> str:
        if self._custom_address is not None:
            return self._custom_address
        return self.controller.address

    def endpoint(self, endpoint=''):
        if len(endpoint)>0 and not endpoint.startswith('/'):
            endpoint='/'+endpoint
        return 'http://'+self.address+endpoint

    @property
    def settings(self) -> TSettings:
        return self.controller.settings

    @property
    def container_parameter(self) -> str|None:
        return self._container_parameter
