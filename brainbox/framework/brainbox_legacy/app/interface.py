from typing import *
from abc import ABC, abstractmethod
from ...job_processing import Job, OperatorLogItem
from typing import *
from ...task import IJobRequestFactory

class IBrainboxService(ABC):
    @abstractmethod
    def base_add(self, jobs: list[dict]):
        pass

    @abstractmethod
    def base_join(self, ids: list[str]) -> list:
        pass

    @abstractmethod
    def result(self, id: str):
        pass

    @abstractmethod
    def job(self, id: str) -> Job:
        pass

    @abstractmethod
    def summary(self, ids: list[str]|None = None, batch_id: str|None = None) -> list[dict]:
        pass

    @abstractmethod
    def cancel(self, job_id: str|None = None, batch_id: str|None = None):
        pass

    @abstractmethod
    def get_operator_log(self, entries_count: int = 100) -> list[OperatorLogItem]:
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def batch_progress(self, batch: str):
        pass

    def add(self, task: Any) -> str|list[str]:
        if isinstance(task, IJobRequestFactory):
            request_stack = [task.to_job_request()]
        else:
            request_stack = []
            for index, e in enumerate(task):
                if isinstance(e, IJobRequestFactory):
                    request_stack.append(e.to_job_request())
                else:
                    raise ValueError(f"Expected IJobRequestFactory, but at index {index} was {e}")

        all_jobs = []
        resulting_ids = []
        for stack in request_stack:
            for job in stack.jobs:
                if job.batch is None:
                    job.batch = stack.main_id
            resulting_ids.append(stack.main_id)
            all_jobs.extend(stack.jobs)

        self.base_add([j.__dict__ for j in reversed(all_jobs)])
        if len(request_stack) == 1:
            return resulting_ids[0]
        else:
            return resulting_ids



    def join(self, task: Union[str, Iterable[str]]):
        if isinstance(task, str):
            ids = [task]
            not_list = True
        else:
            try:
                ids = list(task)
            except:
                raise ValueError(f"Task is expected to be str (job id), IBrainBoxTask or Iterable, but was {task}")
            not_list = False
        result = self.base_join(ids)
        if not_list:
            return result[0]
        return result

    def execute(self, task: Any) -> Any:
        ids = self.add(task)
        return self.join(ids)


