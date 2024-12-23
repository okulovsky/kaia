from .decider_instance_key import DeciderInstanceKey
from dataclasses import dataclass
from datetime import datetime

@dataclass
class JobForPlanner:
    id: str
    decider: str
    decider_parameters: str|None
    received_timestamp: datetime
    assigned: bool
    ordering_token: str|None

    def get_decider_instance_key(self):
        return DeciderInstanceKey(self.decider, self.decider_parameters)