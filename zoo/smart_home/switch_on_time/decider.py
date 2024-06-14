from .settings import *
from .space import Space

class Decider:
    def __init__(self, schedule: List[ScheduledSwitch]):
        self.schedule = schedule

    def __call__(self, space: Space):
        if space.timestamp.last_value is None or space.timestamp.current_value is None:
            return
        for item in self.schedule:
            if item.time.intersects_with_interval(space.timestamp.last_value, space.timestamp.current_value):
                space.switch_request.current_value = item.switch_to_state
                break
