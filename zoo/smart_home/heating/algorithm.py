from typing import *
from kaia.bro import amenities as am
from kaia.bro.core import BroAlgorithm, BroAlgorithmPresentation
from kaia.bro.amenities import conbee
from .space import Space
from dataclasses import dataclass
from .plot import HeatingPlot
from .decider import Decider
from .mock import mock_acutator, mock_heating
from .heating_plan import HeatingPlan
import os


@dataclass
class HeatingSettings:
    name: str
    temperature_sensor_id: Optional[str]
    thermostate_id:str
    algorithm_update_in_ms: int = 60000
    interface_update_in_ms: int = 60000
    plot_update_in_ms: int = 60000
    plans: Optional[Iterable[HeatingPlan]] = None


class Field:
    def __init__(self, arg1, arg2, division=None):
        self.arg1 = arg1
        self.arg2 = arg2
        self.division = division

    def __call__(self, data):
        value = data[self.arg1].get(self.arg2, None)
        if value is None:
            return None
        if self.division is not None:
            value = value/self.division
        return value

def create_algorithm(space: Space, debug: bool, settings: HeatingSettings):
    units = [
        am.Timer(space.timestamp, 10*settings.algorithm_update_in_ms/1000 if debug else None),
        am.SettingsReader(),
        am.SettingsHandler(space.plan_delta, 0)
        ]

    if settings.plans is not None:
        values = [p.name for p in settings.plans]
        space.plan_request.input.values = values

    if not debug:
        units.extend([
            conbee.Reader(space.sensor_data),
            (conbee
             .Parser(space.sensor_data)
             .add_rule(space.temperature_on_thermostat, 'sensors', settings.thermostate_id, Field('state','temperature', 100))
             .add_rule(space.temperature_setpoint, 'sensors', settings.thermostate_id, Field('config','heatsetpoint', 100))
             .add_rule(space.valve_position, 'sensors', settings.thermostate_id, Field('state','valve'))
             .add_rule(space.update_time, 'sensors', settings.thermostate_id, Field('state', 'lastupdated'))
             )
        ])
        if settings.temperature_sensor_id is not None:
            units.append(
                conbee
                .Parser(space.sensor_data)
                .add_rule(space.temperature_on_sensor, 'sensors', settings.temperature_sensor_id, Field('state','temperature', 100))
             )
    else:
        units.append(mock_heating)

    decider = Decider(settings.plans)
    units.append(decider)

    if not debug:
        units.append(conbee.Actuator(
            space.sensor_data,
            'sensors',
            settings.thermostate_id,
            'config',
            'heatsetpoint',
            space.temperature_setpoint_command,
            space.temperature_setpoint_feedback
        ))
    else:
        units.append(mock_acutator)

    algorithm = BroAlgorithm(
        space,
        units,
        min_history_length=8*60,
        update_interval_in_millisecods=settings.algorithm_update_in_ms,
        presentation= BroAlgorithmPresentation(HeatingPlot(), settings.interface_update_in_ms, settings.plot_update_in_ms)
    )
    return algorithm