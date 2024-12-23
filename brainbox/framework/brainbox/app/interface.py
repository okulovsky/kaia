from typing import *
from .task import IBrainBoxTask
from abc import ABC, abstractmethod
from ...job_processing import Job, OperatorLogItem



class _ArrayPostprocessor:
    def __init__(self, index, api, postprocessor = None):
        self.index = index
        self.api = api
        self.postprocessor = postprocessor

    def __call__(self, array):
        result = array[self.index]
        if self.postprocessor is not None:
            result = self.postprocessor(result, self.api)
        return result


class IBrainboxService(ABC):
    @abstractmethod
    def base_add(self, jobs: list[Job]):
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

    def add(self, task: Union[IBrainBoxTask, Iterable[IBrainBoxTask]]):
        if isinstance(task, IBrainBoxTask):
            task.before_add(self)
            task = [task]
        else:
            try:
                task = list(task)
            except:
                raise ValueError(f"task should be IBrainBoxTask or iterable, but was: {task}")
            for index, t in enumerate(task):
                if not isinstance(t, IBrainBoxTask):
                    raise ValueError(f"Expected task at position #{index}, but was {t}")
                t.before_add(self)

        jobs = IBrainBoxTask.to_all_jobs(task)
        self.base_add(jobs)

    def join(self, task: Union[IBrainBoxTask, str, Iterable[Union[IBrainBoxTask, str]]]):
        if isinstance(task, str) or isinstance(task, IBrainBoxTask):
            task = [task]
        else:
            try:
                task = list(task)
            except:
                raise ValueError(f"Task is expected to be str (job id), IBrainBoxTask or Iterable, but was {task}")

        ids = []
        postprocessors = []
        for i, t in enumerate(task):
            if isinstance(t, str):
                ids.append(t)
                postprocessors.append(_ArrayPostprocessor(i, self))
            elif isinstance(t, IBrainBoxTask):
                ids.append(t.get_resulting_id())
                postprocessors.append(_ArrayPostprocessor(i, t.postprocess_result))
            else:
                raise ValueError(f"Error at index {i}: expected str (job id) or IBrainBoxTask, but was {t}")

        result = self.base_join(ids)
        result = [postproc(result) for postproc in postprocessors]
        if len(result) == 1:
            return result[0]
        return result

    def execute(self, task: Union[IBrainBoxTask, Iterable[IBrainBoxTask]]):
        self.add(task)
        return self.join(task)


