from typing import *
from dataclasses import dataclass
from datetime import time
from kaia.infra import ScheduledTime

@dataclass
class ScheduledSwitch:
    time: ScheduledTime
    switch_to_state: bool


@dataclass
class Settings:
    name: str
    switch_id: str
    schedule: List[ScheduledSwitch]
    algorithm_update_in_ms = 60*1000
    interface_update_in_ms = 60*1000
    plot_update_in_ms = 60*1000
