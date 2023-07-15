from ...core import ISpace, Slot
from typing import *
import requests
import json
import os


class Driver:
    _current = None # type: 'Driver'

    @staticmethod
    def authenticate(url):
        # Before running this method, go to
        # localhost:8080, auth via interface, top-left button, Gateway, Advanced, Authenticate App
        response = requests.post(
            url + '/api',
            json=dict(devicetype='laptop', login='yura'))
        js = response.json()
        password = js[0]['success']['username']
        return password

    @staticmethod
    def get_current():
        if Driver._current is not None:
            return Driver._current
        url = os.environ['CONBEE_URL']
        password = os.environ['CONBEE_PASSWORD']
        Driver._current = Driver(url, password)
        return Driver._current


    def __init__(self, address, password):
        self.address = address
        self.password = password

    def _sensors_data(self) -> Any:
        rq_address = '{0}/api/{1}/sensors'.format(self.address, self.password)
        response = requests.get(rq_address)
        if response.status_code!=200:
            raise ValueError('Sensors: Response from ConBee: {0}, {1}'.format(response.status_code,response.text))
        return response.json()

    def _raw_lights_data(self)->Any:
        rq_address = '{0}/api/{1}/lights'.format(self.address, self.password)
        response = requests.get(rq_address)
        if response.status_code != 200:
            raise ValueError('Lights: Response from ConBee: {0}, {1}'.format(response.status_code, response.text))
        return response.json()

    def get_data(self):
        return dict(
            sensors=self._sensors_data(),
            lights=self._raw_lights_data()
        )


    def execute_switch_command(self, switch_key, command: bool):
        rq_address = f'{self.address}/api/{self.password}/lights/{switch_key}/state'
        response = requests.put(rq_address,json={'on':command})
        return response
        #print(response.text)

    def act(self, switch_key, params):
        rq_address = f'{self.address}/api/{self.password}/lights/{switch_key}/state'
        response = requests.put(rq_address, json=params)
        return response
        # print(response.text)


class Reader:
    def __init__(self, slot: Union[Slot, str]):
        self.slot_name = Slot.slotname(slot)

    def __call__(self, space: ISpace):
        space.get_slot(self.slot_name).current_value = Driver.get_current().get_data()


