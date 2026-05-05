from typing import TypeVar, Generic
from .docker_web_service_controller import DockerWebServiceController
from ..architecture import TSettings
from ...common import ApiUtils, IDecider

TController = TypeVar('TController')

class DockerWebServiceApi(IDecider, Generic[TSettings, TController]):
    def __init__(self, base_url: str|None, container_parameter: str|None = None):
        self._custom_base_url = base_url
        self._controller: DockerWebServiceController|None = None
        self._container_parameter = container_parameter

    @property
    def controller(self) -> TController:
        return self._controller

    @controller.setter
    def controller(self, controller: TController):
        self._controller = controller

    @property
    def base_url(self) -> str:
        if self._custom_base_url is not None:
            return self._custom_base_url
        return self.controller.base_url

    def endpoint(self, endpoint=''):
        if len(endpoint)>0 and not endpoint.startswith('/'):
            endpoint='/'+endpoint
        return self.base_url+endpoint

    @property
    def settings(self) -> TSettings:
        return self.controller.settings

    @property
    def container_parameter(self) -> str|None:
        return self._container_parameter
