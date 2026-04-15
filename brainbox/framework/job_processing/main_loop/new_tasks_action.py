from ..core import ICoreAction, Core
from .check_ready_action import CheckReadyAction
from .tasks_for_planner_sync_with_last_updated import TaskForPlannerSyncWithLastUpdated
from .remove_incorrect_action import RemoveIncorrectJobsAction


class NewTasksAction(ICoreAction):
    def apply(self, core: Core):
        RemoveIncorrectJobsAction().apply(core)
        CheckReadyAction().apply(core)
        TaskForPlannerSyncWithLastUpdated().apply(core)
