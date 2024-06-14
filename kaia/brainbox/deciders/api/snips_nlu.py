from kaia.infra.marshalling_api import MarshallingEndpoint
import requests

class SnipsNLUApi:
    def __init__(self, address: str):
        MarshallingEndpoint.check_address(address)
        self.address = address


    def train(self, profile: str, data: list):
        reply = requests.post(f'http://{self.address}/train', json=dict(profile=profile, data=data))
        if reply.status_code==500:
            raise ValueError(f'Server returned an error\n{reply.text}')

    def parse(self, profile: str, text: str):
        reply = requests.post(f'http://{self.address}/parse', json=dict(profile=profile, text=text))
        if reply.status_code==500:
            raise ValueError(f'Server returned an error\n{reply.text}')
        return reply.json()