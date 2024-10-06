import requests
from ..arch.utils import FileLike
from ...core import IApiDecider
from kaia.dub.rhasspy_utils.rhasspy_handler import RhasspyHandler
from kaia.dub import IntentsPack

class RhasspyKaldi(IApiDecider):
    def __init__(self,
                 address,
                 model: None|str = None
                 ):
        self.address = address
        self.model = model

    def train(self, intents_pack: IntentsPack):
        sentences = RhasspyHandler(intents_pack.templates).ini_file
        custom_words = '\n'.join(f'{k} {v}' for k, v in intents_pack.custom_words.items())
        reply = requests.post(f'http://{self.address}/train/{intents_pack.language}/{intents_pack.name}', json=dict(sentences=sentences, custom_words=custom_words))
        if reply.status_code != 200:
            raise ValueError(f"RhasspyKaldi couldn't train for {intents_pack.language}/{intents_pack.name}\n{reply.text}")
        return reply.json()

    def transcribe(self, file: FileLike.Type):
        if self.model is None:
            raise ValueError("Model was not provided in `decider_parameters`")
        with FileLike(file, self.file_cache) as file:
            reply = requests.post(
                f'http://{self.address}/transcribe/{self.model}',
                files=(
                    ('file', file),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"RhasspyKaldi couldn't transcribe for {self.model}\n{reply.text}")
            return reply.json()

    def phonemes(self, language: str):
        return requests.get(f'http://{self.address}/phonemes/{language}').text

