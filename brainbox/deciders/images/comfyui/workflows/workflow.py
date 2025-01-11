from abc import ABC, abstractmethod
from .....framework import FileLike, File

class IWorkflow:
    @abstractmethod
    def create_workflow_json(self, job_id: str):
        pass


    @abstractmethod
    def get_input_files(self) -> list[FileLike.Type]:
        pass

    def postprocess(self, files: list[File]):
        return files