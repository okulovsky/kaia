from typing import *
from .task import IBrainBoxTask
from abc import ABC, abstractmethod
from ...job_processing import Job, OperatorLogItem
from typing import *
from dataclasses import dataclass

@dataclass
class _ArrayPostprocessor:
    index: int
    api: Any
    postprocessor: Any = None

    def __call__(self, array):
        if self.index is None:
            return None
        result = array[self.index]
        if self.postprocessor is not None:
            result = self.postprocessor(result, self.api)
        return result


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

    def add(self, task: Union[IBrainBoxTask, Iterable[IBrainBoxTask]]) -> str|list[str]:
        if isinstance(task, IBrainBoxTask):
            single = True
            task.before_add(self)
            task = [task]
        else:
            single = False
            try:
                task = list(task)
            except:
                raise ValueError(f"task should be IBrainBoxTask or iterable, but was: {task}")
            for index, t in enumerate(task):
                if not isinstance(t, IBrainBoxTask):
                    raise ValueError(f"Expected task at position #{index}, but was {t}")
                t.before_add(self)

        job_dicts = []
        resulting_ids = []
        for t in task:
            jobs = t.create_jobs()
            batch_id = t.get_resulting_id()
            resulting_ids.append(batch_id)
            for j in jobs:
                j.batch = batch_id
                d = j.__dict__
                del d['_sa_instance_state']
                job_dicts.append(d)

        self.base_add(job_dicts)
        if single:
            return resulting_ids[0]
        else:
            return resulting_ids



    def join(self, task: Union[IBrainBoxTask, str, Iterable[Union[IBrainBoxTask, str]]]):
        if isinstance(task, str) or isinstance(task, IBrainBoxTask):
            task = [task]
            not_list = True
        else:
            try:
                task = list(task)
            except:
                raise ValueError(f"Task is expected to be str (job id), IBrainBoxTask or Iterable, but was {task}")
            not_list = False

        ids = []
        postprocessors = []
        index = 0
        for true_index, t in enumerate(task):
            if isinstance(t, str):
                ids.append(t)
                postprocessors.append(_ArrayPostprocessor(index, self))
                index += 1
            elif isinstance(t, IBrainBoxTask):
                id = t.get_resulting_id()
                if id is None:
                    postprocessors.append(_ArrayPostprocessor(None, self))
                else:
                    ids.append(t.get_resulting_id())
                    postprocessors.append(_ArrayPostprocessor(index, self, t.postprocess_result))
                    index+=1
            else:
                raise ValueError(f"Error at index {true_index}: expected str (job id) or IBrainBoxTask, but was {t}")

        result = self.base_join(ids)
        result = [postproc(result) for postproc in postprocessors]

        if not_list:
            return result[0]
        return result

    def execute(self, task: Union[IBrainBoxTask, Iterable[IBrainBoxTask]]):
        self.add(task)
        return self.join(task)


