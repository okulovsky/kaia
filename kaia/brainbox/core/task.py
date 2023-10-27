from typing import *

class BrainBoxTask:
    def __init__(self,
                 id: str,
                 decider: str,
                 method: str,
                 arguments: Dict,
                 dependencies: Optional[Dict] = None,
                 back_track: Any = None,
                 batch: str = None
                 ):
        self.id = id
        self.decider = decider
        self.method = method
        self.arguments = arguments
        self.dependencies = dependencies
        self.back_track = back_track
        self.batch = batch

    def __repr__(self):
        return self.__dict__.__repr__()

