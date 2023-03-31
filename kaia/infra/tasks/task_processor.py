from typing import *
import dataclasses

@dataclasses.dataclass()
class TaskStatus:
    id: str
    received: bool = False
    arguments: Dict[str,Any] = dataclasses.field(default_factory=lambda:{})
    accepted: bool = False
    progress: Optional[float] = None
    aborted: bool = False
    success: bool = False
    failure: bool = False
    result: Optional = None
    error: Optional[Dict[str,str]] = None
    log: Optional[List[str]] = dataclasses.field(default_factory=lambda:[])

    def finished(self):
        return self.aborted or self.success or self.failure

    def status(self):
        if self.aborted:
            return 'aborted'
        if self.success:
            return 'success'
        if self.failure:
            return 'failure'
        if self.accepted:
            return 'accepted'
        if self.received:
            return 'received'
        return 'unknown'


class TaskProcessor:
    def create_task(self, task_arguments: Dict[str, Any]) -> str:
        raise NotImplementedError()

    def get_status(self, task_id: str) -> TaskStatus:
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
