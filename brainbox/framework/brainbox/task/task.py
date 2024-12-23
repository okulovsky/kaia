from typing import *
from uuid import uuid4
from copy import copy
from ...common import SignatureProcessor
from ..app import IBrainBoxTask
from ...job_processing import Job
from .task_builder import BrainBoxTaskBuilderResult, BrainBoxTaskBuilder
from .helper_methods import fix_decider_and_decider_method, fix_arguments_and_dependencies

TDecider = TypeVar('TDecider')
TValue = TypeVar('TValue')




class BrainBoxTask(IBrainBoxTask):
    def __init__(self,
                 *,
                 decider: Union[str,type,Callable],
                 arguments: Optional[Dict[str,Any]] = None,
                 id: str | None = None,
                 dependencies: Optional[Dict[str,Union[str, 'BrainBoxTask']]] = None,
                 fake_dependencies: Optional[List[Union[str,'BrainBoxTask']]] = None,
                 info: Any = None,
                 batch: str|None = None,
                 decider_method: Union[None, str, Callable] = None,
                 decider_parameter: None|str = None,
                 ordering_token: str|None = None,
                 ):
        if id is not None:
            self.id = id
        else:
            self.id = BrainBoxTask.safe_id()

        self.decider, self.decider_method, _method_to_validate = fix_decider_and_decider_method(decider, decider_method)

        self.arguments, self.dependencies = fix_arguments_and_dependencies(arguments, dependencies, fake_dependencies)
        if _method_to_validate is not None:
            SignatureProcessor.from_signature(_method_to_validate).to_kwargs_only(**self.arguments, **self.dependencies)

        self.info = info
        self.batch = batch
        self.decider_parameter = decider_parameter
        self.ordering_token = ordering_token


    def __repr__(self):
        return self.__dict__.__repr__()

    @staticmethod
    def call(_type: Type[TDecider], parameter: str|None = None) -> TDecider:
        return BrainBoxTaskBuilder(_type, parameter=parameter)

    @staticmethod
    def build(call_result: Any) -> BrainBoxTaskBuilderResult:
        return call_result


    def clone(self, **kwargs):
        result = copy(self)
        for k, v in kwargs.items():
            setattr(result, k, v)
        return result

    def get_resulting_id(self) -> str:
        return self.id

    def create_jobs(self) -> list[Job]:
        job = Job(
            id  = self.id,
            decider = self.decider,
            decider_parameter = self.decider_parameter,
            method = self.decider_method,
            arguments = self.arguments,
            info = self.info,
            batch = self.batch,
            ordering_token = self.ordering_token,
            dependencies = self.dependencies
        )
        return [job]


