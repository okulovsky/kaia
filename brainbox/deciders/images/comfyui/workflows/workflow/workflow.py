from brainbox.framework import IJobRequestFactory, JobRequest, JobDescription
from abc import ABC, abstractmethod
from typing import Callable
from ...app.interface import IComfyUI
from .substitution import make_substitution, trim_nodes

class IWorkflow(IJobRequestFactory, ABC):
    @abstractmethod
    def create_workflow(self):
        pass

    @abstractmethod
    def create_file_arguments(self):
        pass

    def get_ordering_token(self) -> str | None:
        return None

    @staticmethod
    def input_placeholder(index: int) -> str:
        return IComfyUI.input_placeholder(index)

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

    @staticmethod
    def trim_nodes(js: dict, predicate: Callable[[dict], bool]):
        trim_nodes(js, predicate)

