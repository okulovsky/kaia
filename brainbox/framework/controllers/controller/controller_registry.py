from typing import Iterable, Union, Type
from ...common import IDecider, Loc, Locator
from ..controller import IController, ControllerOverDecider
from ...deployment import Command, LocalExecutor
import json
from pathlib import Path
import importlib
import inspect
from dataclasses import dataclass


@dataclass
class InstallationStatus:
    installed: bool
    dockerless_controller: bool
    size: str|None = None


class ControllerRegistry:
    def __init__(self,
                 controllers: Iterable[Union[IController, IDecider, Type[IController], Type[IDecider]]],
                 locator: Locator = Loc
                 ):
        updated_controllers = []
        for i, c in enumerate(controllers):
            updated_controllers.append(ControllerRegistry.to_controller(c))
        self._controllers = tuple(updated_controllers)
        self._name_to_controller = {c.get_name(): c for c in self._controllers}
        self.locator = locator

    @staticmethod
    def to_controller_name(obj: str|IDecider|IController|type[IDecider]|type[IController]):
        if isinstance(obj, IDecider):
            return type(obj).__name__
        if isinstance(obj, IController):
            return obj.get_name()
        if isinstance(obj, str):
            return obj
        if isinstance(obj, type):
            if issubclass(obj, IDecider):
                return obj.__name__
            if issubclass(obj, IController):
                return obj.__name__.replace("Controller","")
        raise ValueError(f"Expected str or instance/type of IDecider, IController, but was {obj}")

    @staticmethod
    def to_controller(obj: IDecider|IController|type[IDecider]|type[IController]) -> IController:
        if isinstance(obj, IController):
            return obj
        if isinstance(obj, IDecider):
            tp = type(obj)
            if hasattr(tp, 'Controller'):
                return tp.Controller()
            return ControllerOverDecider(obj)
        if isinstance(obj, type):
            if issubclass(obj, IController):
                return obj()
            if issubclass(obj, IDecider):
                if hasattr(obj, 'Controller'):
                    return obj.Controller()
                return ControllerOverDecider(obj())
        raise ValueError(f"Expected instance or type of IDecider or IController, but was {obj}")

    def get_controller(self, name: str) -> IController:
        if name not in self._name_to_controller:
            raise ValueError(f"The requested controller {name} is not in the list of controllers")
        controller = self._name_to_controller[name]
        controller.context._resource_folder_root = self.locator.resources_folder
        return controller

    def get_deciders_names(self) -> list[str]:
        return list(self._name_to_controller)


    def get_installation_statuses(self) -> dict[str, InstallationStatus]:
        executor = LocalExecutor()
        command_output = executor.execute([
            'docker',
            'images',
            '--format',
            """{"repository": "{{.Repository}}", "size": "{{.Size}}"}"""
        ], Command.Options(return_output=True))

        images_data = []
        for s in command_output.split('\n'):
            if s.strip() == '':
                continue
            images_data.append(json.loads(s))

        images = {image['repository']: image for image in images_data}
        images_names = tuple(images)
        result = {}

        for name in self.get_deciders_names():
            container = self.get_controller(name)
            found_image_name = container.find_self_in_list(images_names)
            if found_image_name is None:
                result[name] = InstallationStatus(False, False)
                continue
            if isinstance(found_image_name, IController.DockerlessInstallation):
                result[name ] = InstallationStatus(True, True)
                continue
            if found_image_name not in images:
                raise ValueError(f"Controller breached contract on `find_self_in_list` method, returned {found_image_name}")
            result[name] = InstallationStatus(True, False, images[found_image_name]['size'])

        return result


    @staticmethod
    def discover() -> 'ControllerRegistry':
        module = importlib.import_module('brainbox.deciders')

        classes = [obj for _, obj in inspect.getmembers(module, inspect.isclass)]

        controllers = []
        for c in classes:
            if not isinstance(c, type):
                continue
            if not issubclass(c, IController) and not issubclass(c, IDecider):
                continue
            controllers.append(ControllerRegistry.to_controller(c))

        return ControllerRegistry(controllers)

    @staticmethod
    def discover_or_create(services: Iterable[IDecider|IController]|None):
        if services is None:
            return ControllerRegistry.discover()
        return ControllerRegistry(services)