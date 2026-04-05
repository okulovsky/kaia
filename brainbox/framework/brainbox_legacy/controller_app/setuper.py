from .interface import ControllersSetup, ControllerInstanceSetup
from .service import ControllerService, ControllerServiceStatus, ControllerServiceStatus
from ..controller import ControllerRegistry, ISingleLoadableModelApi
from yo_fluq import Query

class Setuper:
    def __init__(self, setup: ControllersSetup, service: ControllerService):
        self.setup = setup.controllers
        self.service = service

    def find(self, statuses: ControllerServiceStatus, setup: ControllerInstanceSetup) -> tuple[ControllerServiceStatus.Controller, ControllerServiceStatus.Instance|None]:
        name = ControllerRegistry.to_controller_name(setup.decider)
        status = Query.en(statuses.containers).where(lambda z: z.name == name).single()
        for instance in status.instances:
            if instance.parameter == setup.parameter:
                return status, instance
        return status, None

    def _install(self, statuses: ControllerServiceStatus):
        changed = False
        for s in self.setup:
            status, _ = self.find(statuses, s)
            if not status.installation_status.installed:
                self.service.install(s.decider)
                changed = True
        return changed


    def _run(self, statuses: ControllerServiceStatus):
        changed = False
        for s in self.setup:
            status, instance = self.find(statuses, s)
            if instance is None:
                self.service.run(s.decider, s.parameter)
                changed = True
        return changed

    def _load_model(self, statuses: ControllerServiceStatus):
        changed = False
        for s in self.setup:
            _, instance = self.find(statuses, s)
            if instance is None:
                raise ValueError(f"The required service {s.decider} failed to start")

            if s.loaded_model is None:
                continue

            controller = self.service.get_controller(s.decider)
            api = controller.find_api(instance.instance_id)
            if not isinstance(api, ISingleLoadableModelApi):
                raise ValueError(f"Setup for controller {s.decider} expects model {s.loaded_model}, but the decider is not ISingleLoadableModelApi")
            if api.get_loaded_model_name() != s.loaded_model:
                api.load_model(s.loaded_model)
                changed = True
        return changed


    def make_all(self):
        statuses = self.service.status()
        if self._install(statuses):
            statuses = self.service.status()
        if self._run(statuses):
            statuses = self.service.status()
        self._load_model(statuses)
