from brainbox.framework import IJobRequestFactory, JobRequest, JobDescription
from abc import ABC, abstractmethod
from .substitution import make_substitution

class IWorkflow(IJobRequestFactory, ABC):
    @abstractmethod
    def create_workflow(self):
        pass

    @abstractmethod
    def create_file_arguments(self):
        pass

    def get_ordering_token(self) -> str | None:
        return None

    def to_job_request(self) -> 'JobRequest':
        arguments = dict(
            workflow = self.create_workflow()
        )
        file_arguments = self.create_file_arguments()
        for i, file_argument in enumerate(file_arguments):
            arguments[f'input_{i}'] = file_argument

        description = JobDescription(
            decider = "ComfyUI",
            method="workflow",
            arguments = arguments,
            ordering_token = self.get_ordering_token(),
        )
        return JobRequest((description,))

    @staticmethod
    def make_substitution(js: dict, field_name: str, value: object, node_title: str | None = None):
        make_substitution(js, field_name, value, node_title)

