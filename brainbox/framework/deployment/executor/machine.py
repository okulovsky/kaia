from dataclasses import dataclass
from pathlib import Path

@dataclass
class Machine:
    user_id: int
    group_id: int
    ip_address: str
    username: str
    has_gpu: bool

    @staticmethod
    def local():
        return Machine(1000,1000,'127.0.0.1','', True)
