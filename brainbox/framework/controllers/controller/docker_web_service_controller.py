from .docker_controller import DockerController, TSettings
from abc import ABC, abstractmethod
from .run_configuration import RunConfiguration
from .connection_settings import ConnectionSettings
import requests
from ...common import ApiUtils

class DockerWebServiceController(DockerController[TSettings], ABC):
    @abstractmethod
    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        pass

    @abstractmethod
    def create_api(self):
        pass

    @property
    def connection_settings(self) -> ConnectionSettings:
        settings = self.settings
        if not hasattr(settings, 'connection'):
            raise ValueError(f"Settings do not have `connection` field defined, impossible to use with {type(self).__name__}")
        connection = settings.connection
        if not isinstance(connection, ConnectionSettings):
            raise ValueError(f"Settings field `connection` is not of ConnectionSettings type")
        return connection

    def find_api(self, instance_id: str):
        api = self.create_api()
        from .docker_web_service_api import DockerWebServiceApi
        if not isinstance(api, DockerWebServiceApi):
            raise ValueError(f"Unexpected type {api} returned, expected an object of DockerWebServiceApi's subclass")
        api.controller = self
        api._container_parameter = self.instance_id_to_parameter(instance_id)
        return api

    @property
    def address(self) -> str:
        return f'127.0.0.1:{self.connection_settings.port}'

    def endpoint(self, endpoint=''):
        return 'http://'+self.address + endpoint

    def wait_for_boot(self):
        ApiUtils.wait_for_reply(
            self.endpoint(),
            self.connection_settings.loading_time_in_seconds,
            self.get_name()
        )

    def is_reachable(self):
        try:
            reply = requests.get(self.endpoint())
        except:
            return False
        if reply.status_code != 200:
            return False
        return True


    def run(self, parameter: str|None = None):
        self.stop_all()
        container_id = self.run_with_configuration(self.get_service_run_configuration(parameter))
        self.wait_for_boot()
        return container_id


