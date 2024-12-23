from ...job_processing import Job
from .task import IBrainBoxTask
from abc import ABC, abstractmethod

class IOneBrainBoxTaskFactory(IBrainBoxTask, ABC):
    @abstractmethod
    def to_task(self):
        pass

    def create_jobs(self) -> list[Job]:
        return self.to_task().create_jobs()

    def get_resulting_id(self) -> str:
        return self.to_task().get_resulting_id()

    def before_add(self, api):
        return self.to_task().before_add(api)

    def postprocess_result(self, result, api):
        return self.to_task().postprocess_result(result)