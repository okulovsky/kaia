from typing import *
from .task import BrainBoxTask
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

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
