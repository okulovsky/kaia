from typing import *
import requests
from kaia.dub.rhasspy_utils.rhasspy_handler import RhasspyHandler
from pathlib import Path
import subprocess
from kaia.infra import Loc, MarshallingEndpoint
from kaia.dub.core import Utterance, Template
from ..arch.utils import FileLike
from ...core import IApiDecider


class Rhasspy(IApiDecider):
    def __init__(self, address: str, timeout: int = 5):
        MarshallingEndpoint.check_address(address)
        self.address = address
        self.timeout = timeout


    def recognize(self, file:FileLike.Type):
        with FileLike(file, self.file_cache) as stream:
            data = stream.read()
            reply = requests.post(f'http://{self.address}/api/speech-to-intent', data=data, timeout=self.timeout)
            if reply.status_code != 200:
                raise ValueError(f'Rhasspy failed to recognize bytes\n{reply.text}')
            return reply.json()


    def train(self, intents: Iterable[Template]):
        handler = RhasspyHandler(intents)
        ini = handler.ini_file
        result = ''
        reply = requests.post(f'http://{self.address}/api/sentences', data=ini)
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to accept sentences\n{reply.text}')
        result += reply.text + '\n\n'

        reply = requests.post(f'http://{self.address}/api/train')
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to train\n{reply.text}')
        result += reply.text

        return result



    def set_custom_words(self, custom_words: dict[str,str]):
        lines = [f'{k} {v}' for k,v in custom_words.items()]
        dictionary = '\n'.join(lines)
        reply = requests.post(f'http://{self.address}/api/custom-words', data=dictionary, timeout=self.timeout)
        if reply.status_code != 200:
            raise ValueError(f"Rhasspy failed to set up the dictionary\n{reply.text}")
        reply = requests.post(f'http://{self.address}/api/train')
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to train\n{reply.text}')
        return reply.text