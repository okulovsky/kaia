import requests
from foundation_kaia.marshalling import service, FileLike, FileLikeHandler
from foundation_kaia.brainbox_utils import brainbox_endpoint
from ....framework import DockerWebServiceApi, EntryPoint, TaskBuilder, brainbox_file_like_to_bytes_iterable
from .controller import RhasspyKaldiController
from .settings import RhasspyKaldiSettings
from .model import RhasspyKaldiModel


@service
class IRhasspyKaldi:
    @brainbox_endpoint
    def train(self, model: str, language: str, sentences: str, custom_words: dict[str, str]|None = None) -> dict:
        ...

    @brainbox_endpoint
    def transcribe(self, file: FileLike, model: str) -> dict:
        ...

    @brainbox_endpoint
    def phonemes(self, language: str) -> str:
        ...


class RhasspyKaldiApi(DockerWebServiceApi[RhasspyKaldiSettings, RhasspyKaldiController], IRhasspyKaldi):
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

    def transcribe(self, file: FileLike, model: str):
        file_iterable = b''.join(brainbox_file_like_to_bytes_iterable(file, self.cache_folder))
        reply = requests.post(
            f'http://{self.address}/transcribe/{model}',
            files=(('file', file_iterable),)
        )
        if reply.status_code != 200:
            raise ValueError(f"RhasspyKaldi couldn't transcribe for {model}\n{reply.text}")
        return reply.json()

    def phonemes(self, language: str):
        return requests.get(f'http://{self.address}/phonemes/{language}').text


class RhasspyKaldiTaskBuilder(TaskBuilder, IRhasspyKaldi):
    pass


class RhasspyKaldiEntryPoint(EntryPoint[RhasspyKaldiTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = RhasspyKaldiApi
        self.Controller = RhasspyKaldiController
        self.Settings = RhasspyKaldiSettings
        self.Model = RhasspyKaldiModel

    def get_ordering_arguments_sequence(self) -> tuple[str, ...]|None:
        return ('model',)

RhasspyKaldi = RhasspyKaldiEntryPoint()
