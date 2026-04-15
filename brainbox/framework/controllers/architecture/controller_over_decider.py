from typing import Iterable
from unittest import TestCase
from ...common import ISelfManagingDecider
from .controller import IController, TSettings
from uuid import uuid4

class ControllerOverDecider(IController):
    def __init__(self, decider: ISelfManagingDecider):
        self.decider = decider
        self.virtual_instances = {}

    def install(self):
        pass

    def uninstall(self, purge: bool = False):
        pass

    def find_self_in_list(self, all_images_installed: tuple[str,...]) -> str|None|IController.DockerlessInstallation:
        return IController.DockerlessInstallation()

    def get_default_settings(self) -> TSettings:
        return object()

    def run(self, parameter: str|None) -> str:
        self.decider.warmup(parameter)
        instance_id = str(uuid4())
        self.virtual_instances[instance_id] = parameter
        return instance_id

    def stop(self, instance_id: str):
        self.decider.cooldown()
        del self.virtual_instances[instance_id]

    def get_running_instances_id_to_parameter(self) -> dict[str, str|None]:
        return self.virtual_instances

    def get_name(self):
        return self.decider.get_name()

    def find_api(self, instance_id: str):
        return self.decider

    def _self_test_internal(self, api, tc: TestCase) -> Iterable:
        pass
