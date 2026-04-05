from .app import BrainBoxApi
from .task.legacy_task_builder import LegacyTaskBuilder
from .task import IJobRequestFactory

class BrainBox:
    Api = BrainBoxApi
    TaskBuilder = LegacyTaskBuilder
    Task = IJobRequestFactory

