from typing import Optional,Callable,Any
from abc import ABC, abstractmethod
from ..app import BrainBoxApi
from dataclasses import dataclass
from pathlib import Path

class IPostprocessor(ABC):
    @abstractmethod
    def postprocess(self, result, api):
        pass

class DefaultPostprocessor(IPostprocessor):
    def postprocess(self, result, api):
        return result

@dataclass
class DownloadingPostprocessorBase(IPostprocessor):
    take_element_before_downloading: Optional[int] = None

    def postprocess(self, result, api):
        if self.take_element_before_downloading is not None:
            try:
                result = result[self.take_element_before_downloading]
            except Exception as ex:
                raise ValueError(f"Cannot take element {self.take_element_before_downloading} from value {result}") from ex
        return result


_MISSING = object()

@dataclass
class FilePostprocessor(DownloadingPostprocessorBase):
    metadata: Any = _MISSING

    def postprocess(self, result, api):
        result = super().postprocess(result, api)
        file = api.open_file(result)
        if self.metadata is not _MISSING:
            file.metadata = self.metadata
        return file


@dataclass
class DownloadingPostprocessor(DownloadingPostprocessorBase):
    opener: Optional[Callable[[Path], Any]] = None

    def postprocess(self, result, api: BrainBoxApi):
        result = super().postprocess(result, api)
        result = api.download(result)
        if self.opener is not None:
            result = self.opener(result)
        return result
