from dataclasses import dataclass
from .postprocessors import IPostprocessor
from .prerequisites import IPrerequisite
from ..app import IBrainBoxTask
from ...job_processing import Job


@dataclass
class BrainBoxExtendedTask(IBrainBoxTask):
    task: IBrainBoxTask
    prerequisite: IPrerequisite|None = None
    postprocessor: IPostprocessor|None = None

    def __post_init__(self):
        if not isinstance(self.task, IBrainBoxTask):
            raise TypeError("task must be a BrainBoxTask")

    def create_jobs(self) -> list[Job]:
        return self.task.create_jobs()

    def before_add(self, api):
        if self.prerequisite is not None:
            self.prerequisite.execute(api)

    def postprocess_result(self, result, api):
        if self.postprocessor is not None:
            return self.postprocessor.postprocess(result, api)
        return result

    def get_resulting_id(self) -> str|None:
        return self.task.get_resulting_id()



