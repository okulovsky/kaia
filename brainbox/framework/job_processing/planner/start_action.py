from .planner_action import IPlannerAction
from ..core import DeciderInstanceKey, Core, OperatorState, Job
from ..operator import DeciderOperator
from threading import Thread
from ...common import IDecider
from sqlalchemy import select
import traceback
from dataclasses import dataclass
from enum import Enum

@dataclass
class StartCommand(IPlannerAction):
    class Mode(Enum):
        StartOnly = 0
        FindThenStart = 1
        FindOnly = 2

    key: DeciderInstanceKey
    mode: 'StartCommand.Mode'


    def _start(self, controller):
        instance_id = controller.run(self.key.parameter)
        api: IDecider = controller.find_api(instance_id)
        return instance_id, api

    def _use_existing_or_start(self, controller):
        instances = controller.get_running_instances_id_to_parameter()
        instance_id = None
        api = None
        for key, value in instances.items():
            if value == self.key.parameter:
                instance_id = key
                api = controller.find_api(instance_id)

        if instance_id is not None and api is not None:
            return instance_id, api

        if self.mode == StartCommand.Mode.FindOnly:
            if instance_id is None:
                raise ValueError(f"Could not find {self.key} among running instances for {self.key}")
            if api is None:
                raise ValueError(f"Could not find for {self.key}, instance {instance_id}")

        return self._start(controller)


    def apply(self, core: Core):
        core.operator_log.decider(self.key).event(f"Setting up container in the mode {self.mode.name}")
        try:
            controller = core.registry.get_controller(self.key.decider_name)
            if self.mode == StartCommand.Mode.StartOnly:
                instance_id, api = self._start(controller)
            else:
                instance_id, api = self._use_existing_or_start(controller)

            api.context._cache_folder = core.locator.cache_folder
            op_state = OperatorState(
                self.key,
                controller,
                instance_id,
                api,
                core.operator_log,
            )
            operator = DeciderOperator(op_state)
            thread = Thread(target=operator.cycle)
            op_state.operator_thread = thread
            thread.start()
            core.operator_states[instance_id] = op_state
            core.operator_log.decider(self.key).event("Initialized")
        except:
            core.operator_log.decider(self.key).event("Initialization failed")
            with core.new_session() as session:
                tasks: list[Job] = list(session.scalars(
                    select(Job)
                    .where(
                        ~Job.finished &
                        (Job.decider == self.key.decider_name) &
                        (Job.decider_parameter == self.key.parameter)
                    )
                ))
                for task in tasks:
                    if task.get_key() == self.key:
                        core.close_job(session, task, f'Decider {self.key} failed to warm up:\n{traceback.format_exc()}')
                session.commit()