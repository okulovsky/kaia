from kaia.infra.marshalling_api import MarshallingEndpoint
import requests
from pathlib import Path
from io import BytesIO

class WhisperAPI:
    def __init__(self, address: str):
        MarshallingEndpoint.check_address(address)
        self.address = address



    def load_model(self, model_name):
        reply = requests.post(f'http://{self.address}/load_model', json=dict(model=model_name))
        if reply.status_code != 200:
            raise ValueError(reply.text)


    def transcribe(self, file: Path|bytes|str):
        if isinstance(file, Path) or isinstance(file, str):
            stream = open(file, 'rb')
        elif isinstance(file, bytes):
            stream = BytesIO(file)
        else:
            raise ValueError(f'File should be path, str (with path) or bytes, but was: {file}')

        reply = requests.post(
            f'http://{self.address}/transcribe',
            files=(
                ('file', stream),
            )
        )
        if reply.status_code!=200:
            raise ValueError(reply.text)
        return reply.json()

    def transcribe_text_only(self, file: Path|bytes|str):
        result = self.transcribe(file)
        return result.get('text','').strip()
