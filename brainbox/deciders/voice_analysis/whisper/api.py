from ....framework import DockerWebServiceApi, FileLike
from .settings import WhisperSettings
from .controller import WhisperController
import requests
from pathlib import Path
from io import BytesIO
import json



class Whisper(DockerWebServiceApi[WhisperSettings, WhisperController]):
    def __init__(self, address: str = None):
        super().__init__(address)


    def transcribe_json(self,
                        file: FileLike.Type,
                        model: str|None = None,
                        initial_prompt: None|str = None,
                        parameters: None|dict = None
                        ):
        if parameters is None:
            parameters = {}
        if initial_prompt is not None:
            parameters['initial_prompt'] = initial_prompt
        parameters = dict(model = model, parameters = parameters)
        json_file = BytesIO()
        json_file.write(json.dumps(parameters).encode('utf-8'))
        json_file.seek(0)

        with FileLike(file, self.cache_folder) as stream:
            reply = requests.post(
                f'http://{self.address}/transcribe',
                files=(
                    ('file', stream),
                    ('parameters', json_file)
                )
            )
        if reply.status_code!=200:
            raise ValueError(reply.text)
        return reply.json()


    def transcribe(self,
                   file: FileLike.Type,
                   model: str|None = None,
                   initial_prompt: None | str = None,
                   parameters: None | dict = None
                   ):
        result = self.transcribe_json(file, model, initial_prompt, parameters)
        return result.get('text','').strip()


    def load_model(self, model: str):
        reply = requests.post(f'http://{self.address}/load_model', json=dict(model=model))
        if reply.status_code != 200:
            raise ValueError(reply.text)

    def get_loaded_model(self):
        reply = requests.get(f'http://{self.address}/get_loaded_model')
        return reply.json()

    Controller = WhisperController
    Settings = WhisperSettings

    @classmethod
    def get_ordering_arguments_sequence(cls) -> tuple[str,...]|None:
        return ('model',)
