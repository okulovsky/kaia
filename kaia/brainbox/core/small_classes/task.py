from typing import *
from uuid import uuid4
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class BrainBoxTask:
    id: str
    decider: str
    arguments: Dict
    dependencies: Optional[Dict] = None
    back_track: Any = None
    batch: str = None
    decider_method: Optional[str] = None
    decider_parameters: str = None

    def __repr__(self):
        return self.__dict__.__repr__()

    @staticmethod
    def template(decider: str, decider_method: Optional[str] = None, arguments = None, decider_parameters = None):
        if arguments is None:
            arguments = {}
        return BrainBoxTask(id = '', decider=decider, decider_method=decider_method, arguments=arguments, decider_parameters=decider_parameters)

    @staticmethod
    def safe_id():
        return 'id_'+str(uuid4()).replace('-','')


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
