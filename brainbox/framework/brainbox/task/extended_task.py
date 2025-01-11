from dataclasses import dataclass
from .postprocessors import IPostprocessor
from .prerequisites import IPrerequisite
from ..app import IBrainBoxTask
from ...job_processing import Job


@dataclass
class BrainBoxExtendedTask(IBrainBoxTask):
    task: IBrainBoxTask|None = None
    prerequisite: IPrerequisite|None = None
    postprocessor: IPostprocessor|None = None

    def create_jobs(self) -> list[Job]:
        if self.task is not None:
            return self.task.create_jobs()
        return []

    def before_add(self, api):
        if self.prerequisite is not None:
            self.prerequisite.execute(api)

    def postprocess_result(self, result, api):
        if self.postprocessor is not None:
            return self.postprocessor.postprocess(result, api)
        return result

    def get_resulting_id(self) -> str|None:
        if self.task is None:
            return None
        return self.task.get_resulting_id()



