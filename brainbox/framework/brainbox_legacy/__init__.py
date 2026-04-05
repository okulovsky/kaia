from .app import *
from ..task import *
from ..task.legacy_task_builder import LegacyTaskBuilder


class BrainBox:
    Api = BrainBoxApi
    TaskBuilder = LegacyTaskBuilder
