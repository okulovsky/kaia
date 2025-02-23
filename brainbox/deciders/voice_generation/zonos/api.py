from ....framework import DockerWebServiceApi
import requests
from .settings import ZonosSettings
from .controller import ZonosController



class Zonos(DockerWebServiceApi[ZonosSettings, ZonosController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def echo(self, argument: str):
        result = requests.post(
            self.endpoint('/echo'),
            json = dict(
                argument=argument,
            )
        )
        if result.status_code!=200:
            raise ValueError(f"Endpoint /echo returned unexpected status code {result.status_code}\n{result.text}")
        return result.json()

    Settings = ZonosSettings
    Controller = ZonosController
