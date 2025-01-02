from typing import *
from abc import ABC, abstractmethod
from ...job_processing import Job
from uuid import uuid4

class IBrainBoxTask(ABC):
    @abstractmethod
    def create_jobs(self) -> list[Job]:
        pass

    @abstractmethod
    def get_resulting_id(self) -> str|None:
        pass

    def postprocess_result(self, result, api):
        return result

    def before_add(self, api):
        pass

    @staticmethod
    def to_all_jobs(tasks: Iterable['IBrainBoxTask']) -> list[Job]:
        jobs = []
        for task in tasks:
            jobs.extend(task.create_jobs())
        return jobs

    @staticmethod
    def safe_id():
        return 'id_'+str(uuid4()).replace('-','')