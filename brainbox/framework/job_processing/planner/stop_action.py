from .planner_action import IPlannerAction
from dataclasses import dataclass
from ..core import Core

@dataclass
class StopCommand(IPlannerAction):
    instance_id: str

    def apply(self, core: Core):
        op_state = core.operator_states[self.instance_id]
        core.operator_log.decider(op_state.key).event("Stoping")
        op_state.exit_request = True
        op_state.operator_thread.join()
        op_state.controller.stop(self.instance_id)
        del core.operator_states[self.instance_id]
        core.operator_log.decider(op_state.key).event("Stopped")