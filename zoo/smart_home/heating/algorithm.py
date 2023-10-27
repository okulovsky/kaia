from kaia.bro import amenities as am
from kaia.bro.core import BroAlgorithm, BroAlgorithmPresentation
from kaia.bro.amenities import conbee
from .space import Space
from dataclasses import dataclass
from .plot import draw

import os

@dataclass
class HeatingSettings:
    temperature_sensor_id: str
    thermostate_id:str


def create_algorithm(space: Space, debug: bool, settings: HeatingSettings):
    units = [
        am.Timer(space.timestamp, 300 if debug else None),
        ]

    units.extend([
        conbee.Reader(space.sensor_data),
        (conbee
         .Parser(space.sensor_data)
         .add_rule(space.temperature_on_sensor, 'sensors', settings.temperature_sensor_id, lambda z: z['state']['temperature'] / 100)
         .add_rule(space.temperature_on_thermostat, 'sensors', settings.thermostate_id, lambda z: z['state']['temperature'] / 100)
         .add_rule(space.temperature_setpoint, 'sensors', settings.thermostate_id, lambda z: z['config']['heatsetpoint'] / 100)
         .add_rule(space.valve_position, 'sensors', settings.thermostate_id, lambda z: z['state']['valve'])
         )
    ])

    algorithm = BroAlgorithm(
        space,
        units,
        min_history_length=3000,
        update_interval_in_millisecods=100 if debug else 60000,
        presentation= BroAlgorithmPresentation(draw)
    )
    return algorithm