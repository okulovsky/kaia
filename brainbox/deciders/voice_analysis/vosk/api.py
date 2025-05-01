from ....framework import DockerWebServiceApi, FileLike, ISingleLoadableModelApi
import requests
from .settings import VoskSettings
from .controller import VoskController
from .model import VoskModel


class Vosk(DockerWebServiceApi[VoskSettings, VoskController], ISingleLoadableModelApi):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def load_model(self, model_name):
        result = requests.post(self.endpoint('load_model'), json=dict(model=model_name))
        if result.status_code != 200:
            raise ValueError(f"Endpoint load_model returned exception\n{result.text}")


    def get_loaded_model_name(self) -> str|None:
        result = requests.get(self.endpoint('get_loaded_model'))
        if result.status_code != 200:
            raise ValueError(f"Endpoint returned exception\n{result.text}")
        return result.json()


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

    def transcribe_to_string(self, file: FileLike.Type, model_name: str|None = None):
        return ' '.join(z['word'] for z in self.transcribe_to_array(file, model_name))


    Settings = VoskSettings
    Controller = VoskController
    Model = VoskModel
