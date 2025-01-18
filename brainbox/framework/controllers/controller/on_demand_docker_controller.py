from .docker_controller import DockerController, TSettings
from typing import Generic
from abc import ABC, abstractmethod
from .on_demand_docker_api import OnDemandDockerApi

class OnDemandDockerController(DockerController[TSettings]):
    @abstractmethod
    def create_api(self) -> OnDemandDockerApi:
        pass

    def find_api(self, instance_id: str):
        api = self.create_api()
        api.controller = self
        return api

    def run(self, parameter: str|None):
        return 'no-instance'

    def stop(self, instance_id: str):
        self.get_deployment().stop(True)




