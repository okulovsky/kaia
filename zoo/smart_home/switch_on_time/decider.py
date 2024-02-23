from .settings import *
from .space import Space

class Decider:
    def __init__(self, schedule: Dict[time, bool]):
        self.schedule = schedule

    def __call__(self, space: Space):
        if space.timestamp.last_value is None or space.timestamp.current_value is None:
            return
        for time, request in self.schedule.items():
            if space.timestamp.current_value.time() > time and space.timestamp.last_value.time() <= time:
                space.switch_request.current_value = request
                break
