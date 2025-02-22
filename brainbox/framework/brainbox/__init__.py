from .app import *
from .task import *


class BrainBox:
    ITask = IBrainBoxTask
    Api = BrainBoxApi
    Task = BrainBoxTask
    ExtendedTask = BrainBoxExtendedTask
    CombinedTask = BrainBoxCombinedTask
    Command = BrainBoxCommand
