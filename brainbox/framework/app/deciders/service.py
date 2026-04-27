from brainbox.framework.controllers.architecture import ControllerRegistry
from .interface import IDeciderService
from .decider_documentation import DeciderDocumentation


class DeciderService(IDeciderService):
    def __init__(self, registry: ControllerRegistry):
        self.registry = registry

    def decider_doc(self, name: str) -> DeciderDocumentation:
        api_class = self.registry.get_api_class(name)
        controller = self.registry.get_controller(name)
        return DeciderDocumentation.parse(name, api_class, controller)
