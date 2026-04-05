from typing import Iterable, Union, Type

from ...common import IDecider, Loc, Locator, IEntryPoint, ISelfManagingDecider
from .controller import IController
from .controller_over_decider import ControllerOverDecider
from ...deployment import Command, LocalExecutor
import json
import importlib
import inspect
from dataclasses import dataclass


@dataclass
class InstallationStatus:
    installed: bool
    dockerless_controller: bool
    size: str|None = None


ControllerLike = IEntryPoint|IController|ISelfManagingDecider|Type[IController]|Type[ISelfManagingDecider]

class ControllerRegistry:
    def __init__(self,
                 controllers: Iterable[ControllerLike],
                 locator: Locator = Loc
                 ):
        updated_controllers = []
        for i, c in enumerate(controllers):
            updated_controllers.append(ControllerRegistry.to_controller(c))
        self._controllers = tuple(updated_controllers)
        self._name_to_controller = {c.get_name(): c for c in self._controllers}
        self.locator = locator

    @staticmethod
    def to_controller_name(obj: str|ControllerLike):
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, IEntryPoint):
            return type(obj).__name__.replace('EntryPoint','')
        elif isinstance(obj, IController):
            return obj.get_name()
        elif isinstance(obj, ISelfManagingDecider):
            return obj.get_name()
        elif isinstance(obj, type):
            if issubclass(obj, IController):
                return obj.__name__.replace("Controller","")
            elif issubclass(obj, ISelfManagingDecider):
                return obj().get_name()

        raise ValueError(f"Expected str or instance/type of IEntryPoint, IController, ISelfManagingDecider but was {obj}")

    @staticmethod
    def to_controller(obj: ControllerLike) -> IController:
        if isinstance(obj, IController):
            return obj
        if isinstance(obj, ISelfManagingDecider):
            return ControllerOverDecider(obj)
        if isinstance(obj, IEntryPoint):
            if hasattr(obj, 'Controller'):
                t = obj.Controller
                if not isinstance(t, type):
                    raise ValueError(f"Expected EntryPoint.Controller to be type, but was {t}")
                if not issubclass(t, IController):
                    raise ValueError("Expected EntryPoint.Controller to be a type derived from IController")
                return t()
            else:
                raise ValueError("EntryPoint object does not have a 'Controller' field with the controller type")
        if isinstance(obj, type):
            if issubclass(obj, IController):
                return obj()
            if issubclass(obj, IDecider):
                return ControllerOverDecider(obj())
        raise ValueError(f"Expected instance or type of ISelfManagingDecider, IController, or IEntryPoint, but was {obj}")

    def get_controller(self, name: str) -> IController:
        if name not in self._name_to_controller:
            raise ValueError(f"The requested controller {name} is not in the list of controllers")
        controller = self._name_to_controller[name]
        controller.context._resource_folder_root = self.locator.resources_folder
        return controller

    def get_api_class(self, name: str) -> type | None:
        controller = self.get_controller(name)
        if isinstance(controller, ControllerOverDecider):
            return type(controller.decider)
        elif hasattr(controller, 'create_api'):
            return type(controller.create_api())
        return None

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
        controllers = []
        names = set()

        definitions = [obj for _, obj in inspect.getmembers(module)]
        for d in definitions:
            to_add = False
            if isinstance(d, IEntryPoint):
                to_add = True
            elif isinstance(d, type):
                if issubclass(d, IController) or issubclass(d, ISelfManagingDecider):
                    to_add = True
            if not to_add:
                continue
            name = ControllerRegistry.to_controller_name(d)
            if name in names:
                raise ValueError(f"Duplicating controller definition for {name}")
            names.add(name)
            controllers.append(ControllerRegistry.to_controller(d))

        return ControllerRegistry(controllers)

    @staticmethod
    def discover_or_create(services: Iterable[ControllerLike]|None):
        if services is None:
            return ControllerRegistry.discover()
        return ControllerRegistry(services)