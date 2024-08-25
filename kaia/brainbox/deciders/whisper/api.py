from kaia.infra.marshalling_api import MarshallingEndpoint
import requests
from pathlib import Path
from io import BytesIO
import json
from ..arch.utils import FileLike
from ...core import IApiDecider


class Whisper(IApiDecider):
    def __init__(self, address: str):
        MarshallingEndpoint.check_address(address)
        self.address = address


    def transcribe_json(self,
                        file: Path|bytes|str,
                        initial_prompt: None|str = None,
                        parameters: None|dict = None
                        ):
        if parameters is None:
            parameters = {}
        if initial_prompt is not None:
            parameters['initial_prompt'] = initial_prompt
        json_file = BytesIO()
        json_file.write(json.dumps(parameters).encode('utf-8'))
        json_file.seek(0)

        with FileLike(file, self.file_cache) as stream:
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
                   file: Path|bytes|str,
                   initial_prompt: None | str = None,
                   parameters: None | dict = None
                   ):
        result = self.transcribe_json(file, initial_prompt, parameters)
        return result.get('text','').strip()


class WhisperExtendedAPI(Whisper):
    def __init__(self, address):
        super().__init__(address)

    def load_model(self, model_name):
        reply = requests.post(f'http://{self.address}/load_model', json=dict(model=model_name))
        if reply.status_code != 200:
            raise ValueError(reply.text)

    def get_loaded_model(self):
        reply = requests.get(f'http://{self.address}/get_loaded_model')
        return reply.json()

