from typing import *
from ..core import IDecider
import subprocess
import requests
from urllib.parse import urlencode
from uuid import uuid4
from dataclasses import dataclass
import time
from ...infra import subprocess_call
from .docker_based import initialize

@dataclass
class OpenTTSSettings:
    image_name: str = 'synesthesiam/opentts:en'
    port: int = 5500
    name: str = 'opentts'
    dont_cooldown: bool = True


class OpenTTS(IDecider):
    def __init__(self, settings: OpenTTSSettings):
        self.settings = settings

    def warmup(self, parameters: str):
        run_arguments = [
            'docker','run','--name',self.settings.name, '-d','-it',
            '-p', f'5500:{self.settings.port}', self.settings.image_name
        ]
        initialize(self.settings.image_name, run_arguments, 5, 'http://127.0.0.1:5500')


    def cooldown(self, parameters: str):
        if not self.settings.dont_cooldown:
            subprocess.call(f'docker rm $(docker stop $(docker ps -a -q --filter name=^/{self.settings.name} --format="{{{{.ID}}}}"))')


    def __call__(self,
                 text: str,
                 voice: str = 'coqui-tts:en_vctk',
                 lang: str = 'en',
                 speakerId: Optional[str] = 'p256'):
        parameters = dict(text=text, voice=voice, lang=lang, speakerId=speakerId)
        query_string = urlencode(parameters)
        reply = requests.get(f'http://127.0.0.1:{self.settings.port}/api/tts?' + query_string)
        if reply.status_code != 200:
            raise ValueError(f'OpenTTS server returned {reply.status_code}\n{reply.text}')
        fname = f'{uuid4()}.wav'
        with open(self.file_cache/fname, 'wb') as file:
            file.write(reply.content)
        return [fname]





