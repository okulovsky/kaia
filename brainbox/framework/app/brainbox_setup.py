from ..task import LegacyTaskBuilder
from ..controllers import ControllerRegistry, ControllerLike
from .controllers import ControllerInstance
from dataclasses import dataclass, field
from loguru import logger
from .api import BrainBoxApi
from foundation_kaia.brainbox_utils.models import IModelLoadingSupport


@dataclass
class BrainBoxSetup:
    simple_deciders: list[str] = field(default_factory=list)
    deciders_with_model: dict[str, str] = field(default_factory=dict)
    deciders_with_parameters: dict[str, str] = field(default_factory=dict)

    def up(self, decider: ControllerLike, *, model: str | None = None,
           parameter: str | None = None) -> 'BrainBoxSetup':
        name = ControllerRegistry.to_controller_name(decider)
        if model is not None:
            self.deciders_with_model[name] = model
        elif parameter is not None:
            self.deciders_with_parameters[name] = parameter
        else:
            self.simple_deciders.append(name)
        return self

    def _start_decider(self, api: BrainBoxApi, decider: str, parameter: str | None, is_running: bool):
        if is_running:
            logger.info(f"Decider {decider} is running")
        else:
            logger.info(f"Decider {decider} is not running, starting...")
            api.controllers.run(decider, parameter)
            logger.info(f"Decider {decider} is started")

    def _instantiate(self, api: BrainBoxApi, decider_to_instances: dict[str, list[ControllerInstance]]):
        for decider in self.simple_deciders:
            self._start_decider(api, decider, None, decider in decider_to_instances)

        for decider, parameter in self.deciders_with_parameters.items():
            if decider not in decider_to_instances:
                is_running = False
            elif parameter not in [i.parameter for i in decider_to_instances[decider]]:
                is_running = False
            else:
                is_running = True
            self._start_decider(api, decider, parameter, is_running)

        for decider, model in self.deciders_with_model.items():
            self._start_decider(api, decider, None, decider in decider_to_instances)
            task = LegacyTaskBuilder.call(IModelLoadingSupport).load_model(model)
            task.decider = decider
            api.execute(task)


    def _monitor_side_proces(self, api, key):
        is_error = False
        for item in api.follow_report(key):
            logger.info(f'[{item.timestamp}] {item.line}')
            if item.is_error:
                is_error = True
        return not is_error

    def _install(self, api: BrainBoxApi, installed: set[str]):
        all_deciders = (
            self.simple_deciders +
            list(self.deciders_with_model.keys()) +
            list(self.deciders_with_parameters.keys())
        )

        for decider in all_deciders:
            if decider in installed:
                logger.info(f"Decider {decider} already installed")
            else:
                logger.info(f"Installing decider {decider}...")
                key = api.controllers.install.start(decider)
                if not self._monitor_side_proces(api.controllers.install, key):
                    logger.info(f"Installation of {decider} failed")
                    break
                else:
                    logger.info(f"Installation of {decider} is completed")

                logger.info(f"Self-testing decider {decider}...")
                key = api.controllers.self_test.start(decider)
                if not self._monitor_side_proces(api.controllers.self_test, key):
                    logger.info(f"Self-testing decider {decider} failed")
                    break
                else:
                    logger.info(f"Self-testing decider {decider} is completed")



    def execute(self, api: BrainBoxApi):
        logger.info(f"Setting up BrainBox at {api.base_url}")
        status = api.controllers.status()
        installed = {c.name for c in status.controllers if c.installed}

        self._install(api, installed)

        decider_to_instances = {
            c.name: c.instances
            for c in status.controllers
            if len(c.instances) > 0
        }

        self._instantiate(api, decider_to_instances)

