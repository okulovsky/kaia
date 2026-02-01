import json

from ....framework import DockerWebServiceApi, FileLike, File
import requests
from .settings import CosyVoiceSettings
from .controller import CosyVoiceController


class CosyVoice(DockerWebServiceApi[CosyVoiceSettings, CosyVoiceController]):
    def __init__(self, address: str | None = None):
        super().__init__(address)

    def train(self, voice: str,  text: str, file: FileLike.Type):
        with FileLike(file, self.cache_folder) as content:
            reply = requests.post(
                self.endpoint('/train'),
                data=dict(settings=json.dumps(dict(voice=voice, text=text))),
                files=(
                    ('file', content),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"Endpoint returned error \n{reply.text}")
            return reply.text


    def voice_to_file(self, voice: str, file: FileLike.Type):
        with FileLike(file, self.cache_folder) as content:
            reply = requests.post(
                self.endpoint('/voice_to_file'),
                data = dict(settings=json.dumps(dict(voice=voice))),
                files=(
                    ('file', content),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"Endpoint returned error \n{reply.text}")
            return File(
                self.current_job_id + '.output.wav',
                reply.content,
                File.Kind.Audio
            )

    def voice_to_text(self, voice: str, text: str):
        reply = requests.post(
            self.endpoint('/voice_to_text'),
            data = dict(settings=json.dumps(dict(voice=voice, text=text))),
        )
        if reply.status_code != 200:
            raise ValueError(f"Endpoint returned error \n{reply.text}")
        return File(
            self.current_job_id + '.output.wav',
            reply.content,
            File.Kind.Audio
        )

    def voice_to_text_transligual(self, voice: str, text: str):
        reply = requests.post(
            self.endpoint('/voice_to_text_translingual'),
            data = dict(settings=json.dumps(dict(voice=voice, text=text))),
        )
        if reply.status_code != 200:
            raise ValueError(f"Endpoint returned error \n{reply.text}")
        return File(
            self.current_job_id + '.output.wav',
            reply.content,
            File.Kind.Audio
        )

    Settings = CosyVoiceSettings
    Controller = CosyVoiceController
