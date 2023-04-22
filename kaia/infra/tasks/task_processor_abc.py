from typing import *
from .task_cycle import TaskResult




class ITaskProcessor:
    def create_task(self, task_arguments: Dict[str, Any]) -> str:
        raise NotImplementedError()

    def get_status(self, task_id: str) -> TaskResult:
        raise NotImplementedError()

    def get_active_tasks(self) -> List[str]:
        raise NotImplementedError()

    def abort_task(self, task_id: str):
        raise NotImplementedError()

    def is_finished(self, task_id: str) -> bool:
        raise NotImplementedError()

    def activate(self):
        pass

    def deactivate(self):
        pass

    def is_alive(self, timeout_in_seconds):
        return True