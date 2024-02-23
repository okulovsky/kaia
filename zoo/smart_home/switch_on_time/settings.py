from typing import *
from dataclasses import dataclass
from datetime import time


@dataclass
class Settings:
    name: str
    switch_id: str
    schedule: Dict[time, bool]
    algorithm_update_in_ms = 60*1000
    interface_update_in_ms = 60*1000
    plot_update_in_ms = 60*1000
