from typing import Iterable
from unittest import TestCase

from . import TestReport
from ...common import IDecider, ISelfManagingDecider
from .controller import IController, TSettings
from uuid import uuid4


class ControllerOverDecider(IController):
    def __init__(self,
                 decider: IDecider,
                 custom_name: str|None = None
                 ):
        self.decider = decider
        self.custom_name = custom_name
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
        if isinstance(self.decider, ISelfManagingDecider):
            self.decider.warmup(parameter)
        instance_id = str(uuid4())
        self.virtual_instances[instance_id] = parameter
        return instance_id

    def stop(self, instance_id: str):
        if isinstance(self.decider, ISelfManagingDecider):
            return self.decider.cooldown()
        del self.virtual_instances[instance_id]

    def get_running_instances_id_to_parameter(self) -> dict[str, str|None]:
        return self.virtual_instances

    def get_name(self):
        if self.custom_name is not None:
            return self.custom_name
        if hasattr(self.decider, 'get_custom_decider_name'):
            return self.decider.get_custom_decider_name()
        return type(self.decider).__name__

    def find_api(self, instance_id: str):
        return self.decider

    def _self_test_internal(self, tc: TestCase) -> Iterable:
        pass



