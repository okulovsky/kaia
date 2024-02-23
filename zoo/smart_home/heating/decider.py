from typing import *
from .space import Space
from .heating_plan import HeatingPlan

def prettify_temperature(val: float) -> int:
    if val is None:
        return 2000
    return int(100*int(val*2)//2)

class Decider:
    def __init__(self, plans: Optional[Iterable[HeatingPlan]]):
        if plans is not None:
            self.plans = {p.name: p for p in plans} #type: Dict[str, HeatingPlan]
        else:
            self.plans = None

    def __call__(self, space: Space):
        if space.temperature_setpoint_request.current_value is not None:
            val = space.temperature_setpoint_request.current_value
            space.temperature_setpoint_command.current_value = prettify_temperature(val)
            space.plan.current_value = None
            return

        if (
                space.temperature_setpoint.current_value!=space.temperature_setpoint.last_value
            and prettify_temperature(space.temperature_setpoint.current_value) != space.temperature_setpoint_command.last_value
        ):
            space.plan.current_value = None
            return



        if self.plans is not None:
            if space.plan_request.current_value is not None and space.plan_request.current_value in self.plans:
                space.plan.current_value = space.plan_request.current_value
            else:
                space.plan.current_value = space.plan.last_value


            plan_known = space.plan.current_value is not None and space.plan.current_value in self.plans

            if plan_known:
                plan = self.plans[space.plan.current_value] #type: HeatingPlan
                time = space.timestamp.current_value.time()
                temperature = plan.get_value_for(time)
                temperature += space.plan_delta.current_value
                if temperature != space.temperature_setpoint.current_value:
                    space.temperature_setpoint_command.current_value = prettify_temperature(temperature)














