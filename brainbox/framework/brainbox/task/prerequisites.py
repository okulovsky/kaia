from typing import Iterable
from abc import ABC, abstractmethod
from ..app import BrainBoxApi
from ...common import FileLike, File
from pathlib import Path
from dataclasses import dataclass

class IPrerequisite(ABC):
    @abstractmethod
    def execute(self, api: BrainBoxApi):
        pass

@dataclass
class ResourcePrerequisite(IPrerequisite):
    decider: type|str
    resource_path: str
    content: bytes|Path|File|None = None

    def execute(self, api: BrainBoxApi):
        if self.content is None:
            api.controller_api.delete_resource(self.decider, self.resource_path, True)
        else:
            api.controller_api.upload_resource(self.decider, self.resource_path, self.content)


@dataclass
class CacheUploadPrerequisite(IPrerequisite):
    content: FileLike.Type
    file_name: str|None = None

    def execute(self, api: BrainBoxApi):
        filename = self.file_name
        if filename is None:
            filename = FileLike.get_name(self.content, True)
        api.upload(filename, self.content)


class CombinedPrerequisite(IPrerequisite):
    def __init__(self, prereq: Iterable[IPrerequisite]):
        self.prereq = tuple(prereq)

    def execute(self, api: BrainBoxApi):
        for prereq in self.prereq:
            prereq.execute(api)