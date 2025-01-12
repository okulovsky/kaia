from ....framework import DockerWebServiceApi
import requests
from .settings import EspeakPhonemizerSettings
from .controller import EspeakPhonemizerController



class EspeakPhonemizer(DockerWebServiceApi[EspeakPhonemizerSettings, EspeakPhonemizerController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def phonemize(self, text: str|list[str], language: str = 'en-us', stress = False):
        if isinstance(text, str):
            text = [text]

        result = requests.post(
            self.endpoint('/echo'),
            json = dict(
                text = text,
                language = language,
                stress = stress,
            )
        )
        if result.status_code!=200:
            raise ValueError(f"Endpoint /phonemize returned unexpected status code {result.status_code}\n{result.text}")
        return result.json()

    Settings = EspeakPhonemizerSettings
    Controller = EspeakPhonemizerController
