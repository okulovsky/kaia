from ..core import ICoreAction, Core
from .task_status_updater import TasksStatusUpdater
from .check_ready_action import CheckReadyAction
from .tasks_for_planner_sync_with_last_updated import TaskForPlannerSyncWithLastUpdated


class TaskFinishedAction(ICoreAction):
    def apply(self, core: Core):
        TasksStatusUpdater().apply(core)
        CheckReadyAction().apply(core)
        TaskForPlannerSyncWithLastUpdated().apply(core)
