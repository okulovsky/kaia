from typing import *
from dataclasses import dataclass
from ..app import IBrainBoxTask, BrainBoxApi
from ...job_processing import Job

@dataclass
class BrainBoxCombinedTask(IBrainBoxTask):
    resulting_task: IBrainBoxTask
    intermediate_tasks: Tuple[IBrainBoxTask, ...] = ()

    def create_jobs(self) -> list[Job]:
        jobs = IBrainBoxTask.to_all_jobs(self.intermediate_tasks)
        if self.resulting_task is not None:
            jobs.extend(self.resulting_task.create_jobs())
        return jobs

    def get_resulting_id(self) -> str|None:
        if self.resulting_task is None:
            return None
        else:
            return self.resulting_task.get_resulting_id()

    def postprocess_result(self, result, api):
        return self.resulting_task.postprocess_result(result, api)

    def before_add(self, api: BrainBoxApi):
        for task in self.intermediate_tasks:
            task.before_add(api)
        if self.resulting_task is not None:
            self.resulting_task.before_add(api)

