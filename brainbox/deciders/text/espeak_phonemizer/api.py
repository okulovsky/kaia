import json
import uuid

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

    def phonemize_to_file(self, text: str|list[str], language: str = 'en-us', stress = False):
        result = self.phonemize(text, language, stress)
        filename = str(uuid.uuid4())+'.json'
        with open(self.cache_folder/filename, 'w') as f:
            json.dump(result, f)
        return filename

    Settings = EspeakPhonemizerSettings
    Controller = EspeakPhonemizerController
