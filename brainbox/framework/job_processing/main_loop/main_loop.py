import time
import traceback

from ..core import Core, OperatorStateForPlanner
from .cancel_action import CancelAction
from .command_queue import CommandQueue
from .tasks_for_planner_sync_with_last_updated import TaskForPlannerSyncWithLastUpdated
from .task_status_updater import TasksStatusUpdater
from ..planner import IPlanner, PlannerArguments
from ...job_processing.planner.stop_action import StopCommand
from .dirty_exit_fix import DirtyExitFix
from .task_update_reminder import TaskUpdateReminder
from datetime import datetime

class MainLoop:
    def __init__(self,
                 core: Core,
                 planner: IPlanner,
                 command_queue: CommandQueue,
                 stop_containers_at_termination: bool = True,
                 ):
        self.core = core
        self.planner = planner
        self._terminate_request: bool = False
        self.stop_containers_at_termination = stop_containers_at_termination
        self.command_queue = command_queue
        self.task_update_reminder_last_run: datetime|None = None


    def run(self):
        DirtyExitFix().apply(self.core)
        while True:
            if self._terminate_request:
                break
            try:
                self.one_iteration()
            except:
                message = traceback.format_exc()
                self.core.operator_log.core().error(traceback.format_exc())
                print(message)
            time.sleep(0.001)
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
        task_update_reminder_requested = False

        if self.command_queue is not None:
            while not self.command_queue.empty():
                action = self.command_queue.get_nowait()
                if not isinstance(action, TaskUpdateReminder):
                    action.apply(self.core)
                else:
                    task_update_reminder_requested = True

        if task_update_reminder_requested:
            if self.task_update_reminder_last_run is None:
                run = True
            elif (datetime.now() - self.task_update_reminder_last_run).total_seconds() > 0.1:
                run = True
            else:
                run = False
            if run:
                TasksStatusUpdater().apply(self.core)
                self.task_update_reminder_last_run = datetime.now()

        if self.core.jobs_for_planner is None:
            TaskForPlannerSyncWithLastUpdated().apply(self.core)

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


