from typing import *
from kaia.bro import amenities as am
from kaia.bro.core import BroAlgorithm, BroAlgorithmPresentation
from kaia.bro.amenities import conbee
from .space import Space
from .decider import Decider
from .settings import Settings
from .plot import Plot


def create_algorithm(space: Space, debug: bool, settings: Settings):
    units = [
        am.Timer(space.timestamp),
    ]

    if not debug:
        units.append(conbee.Reader(space.sensor_data))
        units.append(conbee
         .Parser(space.sensor_data)
         .add_rule(space.switch_state, 'lights', settings.switch_id, lambda z: z['state']['on'])
         )

    units.append(Decider(settings.schedule))

    if not debug:
        units.append(conbee.SwitchActuator(space.switch_request, settings.switch_id))


    algorithm = BroAlgorithm(
        space,
        units,
        min_history_length=8*60,
        update_interval_in_millisecods=settings.algorithm_update_in_ms,
        presentation= BroAlgorithmPresentation(Plot(), settings.interface_update_in_ms, settings.plot_update_in_ms)
    )
    return algorithm