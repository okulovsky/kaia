from typing import *
from kaia.bro.amenities.conbee import Driver, Parser
from kaia.bro.core import ISpace, Slot
from unittest import TestCase
from pprint import pprint
from yo_fluq_ds import FileIO
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Space(ISpace):
    source: Slot[Any] = Slot.field(False)
    humidity: Slot[float] = Slot.field()
    pressure: Slot[float] = Slot.field()
    temperature: Slot[float] = Slot.field()
    switch: Slot[bool] = Slot.field()




class ConbeeTestCase(TestCase):
    def dont_test_conbee_auth(self):
        if 'CONBEE_URL' not in os.environ:
            self.skipTest('Conbee is not available')
        password = Driver.authenticate(os.environ['CONBEE_URL'])
        print(password)

    def test_conbee(self):
        if 'CONBEE_URL' not in os.environ or 'CONBEE_PASSWORD' not in os.environ:
            self.skipTest('Conbee is not available')
        data = Driver.get_current().get_data()
        self.assertIn('sensors', data)
        self.assertIn('lights', data)


    def test_conbee_parser(self):
        space = Space()
        space.source.current_value = FileIO.read_json(Path(__file__).parent/'conbee.json')
        parser = (
            Parser(space.source)
            .add_rule(space.humidity, 'sensors', '00:15:8d:00:02:c1:3c:d4-01-0405', lambda z: z['state']['humidity'] / 100)
            .add_rule(space.temperature, 'sensors', '00:15:8d:00:02:c1:3c:d4-01-0402', lambda z: z['state']['temperature'] / 100)
            .add_rule(space.pressure, 'sensors', '00:15:8d:00:02:c1:3c:d4-01-0403', lambda z: float(z['state']['pressure']))
            .add_rule(space.switch, 'lights', '84:18:26:00:00:10:55:cd-03', lambda z: z['state']['on'])
        )
        parser(space)
        result = space.get_current_values_as_dict()
        del result['source']
        self.assertDictEqual(
            {'humidity': 73.82, 'pressure': 1010.0, 'temperature': 21.93, 'switch': False},
            result
        )







