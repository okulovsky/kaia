from ..app import BrainBoxApi, IBrainBoxTask
from typing import TypeVar, Generic

T = TypeVar("T")

class BrainBoxCommand(Generic[T]):
    def __init__(self, task: IBrainBoxTask):
        self.task = task

    def execute(self, api: BrainBoxApi) -> T:
        return api.execute(self.task)

    def add(self, api: BrainBoxApi):
        api.add(self.task)

    def join(self, api: BrainBoxApi) -> T:
        return api.join(self.task)

