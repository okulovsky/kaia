from typing import *
from uuid import uuid4
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from copy import copy
from .arguments_validator import ArgumentsValidator


T = TypeVar('T')

class BrainBoxTask:
    def __init__(self,
                 *,
                 decider: Union[str,type,Callable],
                 arguments: None|dict = None,
                 id: str | None = None,
                 dependencies: dict|None = None,
                 back_track:Any = None,
                 batch: str = None,
                 decider_method: Union[None, str, Callable] = None,
                 decider_parameters: None|str = None
                 ):
        if id is not None:
            self.id = id
        else:
            self.id = BrainBoxTask.safe_id()

        _method_to_validate = None
        self.decider_method = None
        self.arguments = None

        if isinstance(decider, type):
            self.decider = decider.__name__
        elif isinstance(decider, str):
            self.decider = decider
        elif callable(decider):
            if decider_method is not None:
                raise ValueError("decider is callable, but decider_method is not None. Callable decider sets both decider and decider_method")
            _method_to_validate = decider
            parts = decider.__qualname__.split('.')
            if len(parts) > 2:
                raise ValueError("If `decider` is a function, it must be exactly 2 parts in qualname, Type.Method")
            self.decider = parts[0]
            self.decider_method = parts[1]
        else:
            raise ValueError(f'decider must be str, type, or callable type method, but was {decider}')

        if callable(decider_method):
            self.decider_method = decider_method.__name__
            _method_to_validate = decider_method
        elif isinstance(decider_method, str):
            self.decider_method = decider_method
        elif decider_method is None:
            pass
        else:
            raise ValueError(f'decider must be str, method or None, but was {decider}')

        if self.arguments is None:
            self.arguments = arguments

        if self.arguments is None:
            self.arguments = {}

        if _method_to_validate is not None:
            validator = ArgumentsValidator.from_signature(_method_to_validate)
            array = []
            if self.arguments is not None:
                array.extend(self.arguments)
            if dependencies is not None:
                array.extend(dependencies)
            validator.validate(array)

        self.dependencies = dependencies
        self.back_track = back_track
        self.batch = batch
        self.decider_parameters = decider_parameters


    def __repr__(self):
        return self.__dict__.__repr__()


    @staticmethod
    def call(type: Type[T]) -> T:
        from .task_builder import BrainBoxTaskBuilder
        return BrainBoxTaskBuilder(type)

    @staticmethod
    def safe_id():
        return 'id_'+str(uuid4()).replace('-','')


    def clone(self, **kwargs):
        result = copy(self)
        for k, v in kwargs.items():
            setattr(result, k, v)
        return result



class IPackPostprocessor(ABC):
    @abstractmethod
    def postprocess(self, result, api):
        pass

class DefaultPostprocessor(IPackPostprocessor):
    def postprocess(self, result, api):
        return result

class DownloadingPostprocessor(IPackPostprocessor):
    def __init__(self,
                 take_element_before_downloading: Optional[int] = None,
                 opener: Optional[Callable[[Path], Any]] = None
                 ):
        self.take_element_before_downloading = take_element_before_downloading
        self.opener = opener
    def postprocess(self, result, api):
        if self.take_element_before_downloading is not None:
            try:
                result = result[self.take_element_before_downloading]
            except Exception as ex:
                raise ValueError(f"Cannot take element {self.take_element_before_downloading} from value {result}") from ex
        result = api.download(result)
        if self.opener is not None:
            result = self.opener(result)
        return result


@dataclass
class BrainBoxTaskPack:
    resulting_task: BrainBoxTask
    intermediate_tasks: Tuple[BrainBoxTask, ...] = ()
    postprocessor: IPackPostprocessor = field(default_factory=DefaultPostprocessor)
    uploads: Dict[str, Union[bytes|Path]] = None
