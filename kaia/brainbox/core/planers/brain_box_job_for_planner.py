from dataclasses import dataclass
from datetime import datetime
from ..small_classes import DeciderInstanceSpec

@dataclass
class BrainBoxJobForPlanner:
    id: str
    decider: str
    decider_parameters: str|None
    received_timestamp: datetime
    assigned: bool

    def get_decider_instance_spec(self):
        return DeciderInstanceSpec(self.decider, self.decider_parameters)