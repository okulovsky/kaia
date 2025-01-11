import requests
from ....framework import DockerWebServiceApi, FileLike
from .controller import RhasspyKaldiController
from .settings import RhasspyKaldiSettings
from .model import RhasspyKaldiModel

class RhasspyKaldi(DockerWebServiceApi[RhasspyKaldiSettings, RhasspyKaldiController]):
    def __init__(self, address: str | None = None):
        super().__init__(address)

    def train(self, model: str, language: str, sentences: str, custom_words: dict[str, str]|None = None):
        if custom_words is not None:
            custom_words_str = '\n'.join(f'{k} {v}' for k, v in custom_words.items())
        else:
            custom_words_str = ''
        reply = requests.post(f'http://{self.address}/train/{language}/{model}', json=dict(sentences=sentences, custom_words=custom_words_str))
        if reply.status_code != 200:
            raise ValueError(f"RhasspyKaldi couldn't train for {language}/{model}\n{reply.text}")
        return reply.json()

    def transcribe(self, file: FileLike.Type, model: str):
        with FileLike(file, self.cache_folder) as file:
            reply = requests.post(
                f'http://{self.address}/transcribe/{model}',
                files=(
                    ('file', file),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"RhasspyKaldi couldn't transcribe for {model}\n{reply.text}")
            return reply.json()

    def phonemes(self, language: str):
        return requests.get(f'http://{self.address}/phonemes/{language}').text

    Controller = RhasspyKaldiController
    Settings = RhasspyKaldiSettings
    Model = RhasspyKaldiModel

    @classmethod
    def get_ordering_arguments_sequence(cls) -> tuple[str,...]|None:
        return ('model',)


'''

`[order]
_order = Shi|Ukha|Borsh
I order <_order>{_order}`
`shi S i
ukha u h 'A
borsh b o r S`

'''