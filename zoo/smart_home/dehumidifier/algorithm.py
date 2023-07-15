from kaia.bro import amenities as am
from kaia.bro.core import BroAlgorithm, BroAlgorithmPresentation
from kaia.bro.amenities import conbee
from zoo.smart_home.dehumidifier.space import Space
from zoo.smart_home.dehumidifier.decider import decider
from . import mocks
from .plot import draw

import os


def create_algorithm(space: Space, debug: bool, settings):


    units = [
        am.Timer(space.timestamp, 300 if debug else None),
        am.SettingsReader(),
        am.SettingsHandler(space.low_humidity, 50),
        am.SettingsHandler(space.high_humidity, 80),
        am.SettingsHandler(space.max_running_time, 120),
        am.SettingsHandler(space.min_cooldown_time, 60),
    ]

    if debug:
        units.append(mocks.MockHumidity(1, -2))
    else:
        units.extend([
            conbee.Reader(space.sensor_data),
            (conbee
             .Parser(space.sensor_data)
             .add_rule(space.humidity, 'sensors', settings.humidity_sensor_id, lambda z: z['state']['humidity'] / 100)
             .add_rule(space.state, 'lights', settings.dehumidifier_sensor_id, lambda z: z['state']['on'])
             )
        ])

    if debug:
        units.append(mocks.MockDehumidifier())

    units.append(decider)

    if not debug:
        units.append(conbee.SwitchActuator(space.state_request, settings.dehumidifier_switch_id))

    presentation = BroAlgorithmPresentation(draw)

    algorithm = BroAlgorithm(
        space,
        units,
        min_history_length=3000,
        update_interval_in_millisecods= 100 if debug else 60000,
        presentation = presentation
    )
    return algorithm
