from ....framework import DockerWebServiceApi, FileLike
import requests
from .settings import VoskSettings
from .controller import VoskController
from .model import VoskModel


class Vosk(DockerWebServiceApi[VoskSettings, VoskController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def load_model(self, model_name):
        result = requests.post(self.endpoint('load_model'), json=dict(model_name=model_name))
        if result.status_code != 200:
            raise ValueError(f"Endpoint load_model returned exception\n{result.text}")

    def transcribe(self, file: FileLike.Type, model_name: str|None = None):
        with FileLike(file, self.cache_folder) as stream:
            ep = 'transcribe'
            if model_name is not None:
                ep+='/'+model_name
            result = requests.post(
                self.endpoint('transcribe/'+model_name),
                files=(
                    ('file', stream),
                ))
            if result.status_code != 200:
                raise ValueError(f"Endpoint transcribe returned error\n{result.text}")
            return result.json()

    def transcribe_to_array(self, file: FileLike.Type, model_name: str|None = None):
        result = self.transcribe(file, model_name)
        return [item for part in result for item in part['result']]

    Settings = VoskSettings
    Controller = VoskController
    Model = VoskModel
