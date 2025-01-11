import time
import traceback

from ..core import Core, OperatorStateForPlanner
from .check_ready_action import CheckReadyAction
from .remove_incorrect_action import RemoveIncorrectJobsAction
from .tasks_for_planner_sync import TaskForPlannerSync
from .task_status_updater import TasksStatusUpdater
from .cancel_action import CancelAction
from ..planner import IPlanner, PlannerArguments
from ...job_processing.planner.stop_action import StopCommand

class MainLoop:
    def __init__(self,
                 core: Core,
                 planner: IPlanner,
                 stop_containers_at_termination: bool = True
                 ):
        self.core = core
        self.planner = planner
        self._terminate_request: bool = False
        self.stop_containers_at_termination = stop_containers_at_termination

    def run(self):
        while True:
            if self._terminate_request:
                break
            try:
                self.one_iteration()
            except:
                message = traceback.format_exc()
                self.core.operator_log.core().error(traceback.format_exc())
                print(message)
            time.sleep(0.1)
        if self.stop_containers_at_termination:
            for state in list(self.core.operator_states.values()):
                try:
                    StopCommand(state.controller_run_instance_id).apply(self.core)
                except:
                    pass



    def terminate(self):
        self._terminate_request = True



    def cancel(self, job_id: str|None = None, batch_id: str|None = None):
        CancelAction(job_id, batch_id).apply(self.core)


    def one_iteration(self):
        RemoveIncorrectJobsAction().apply(self.core)
        TasksStatusUpdater().apply(self.core)
        CheckReadyAction().apply(self.core)
        TaskForPlannerSync().apply(self.core)

        for action in self._run_planner():
            action.apply(self.core)


    def _run_planner(self):
        states_for_planner = tuple(
            OperatorStateForPlanner(instance_id, state.key, state.busy, state.not_busy_since)
            for instance_id, state
            in self.core.operator_states.items()
        )

        planner_arguments = PlannerArguments(
            tuple(job for job in self.core.jobs_for_planner),
            states_for_planner,
            self.core.operator_log.planer()
        )

        return self.planner.plan(planner_arguments)


