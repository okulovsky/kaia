from .planner_action import IPlannerAction
from ..core import DeciderInstanceKey, Core, OperatorState, Job
from ..operator import DeciderOperator
from threading import Thread
from ...common import IDecider
from sqlalchemy import select
import traceback
from dataclasses import dataclass


@dataclass
class StartCommand(IPlannerAction):
    key: DeciderInstanceKey
    use_existing: bool = False

    def apply(self, core: Core):
        core.operator_log.decider(self.key).event("Finding existing" if self.use_existing else "Starting")
        try:
            controller = core.registry.get_controller(self.key.decider_name)

            instance_id = None
            api = None

            if self.use_existing:
                instances = controller.get_running_instances_id_to_parameter()
                for key, value in instances.items():
                    if value == self.key.parameter:
                        instance_id = key
                        api = controller.find_api(instance_id)
                if instance_id is None:
                    raise ValueError(f"Could not find {self.key} among running instances for {self.key}")
                if api is None:
                    raise ValueError(f"Could not find for {self.key}, instance {instance_id}")
            else:
                instance_id = controller.run(self.key.parameter)
                api: IDecider = controller.find_api(instance_id)

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