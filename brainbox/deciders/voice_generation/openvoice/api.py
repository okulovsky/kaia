import os
import shutil

import requests
from ....framework import DockerWebServiceApi, File, FileLike
from .controller import OpenVoiceController
from .settings import OpenVoiceSettings
from typing import Iterable


class OpenVoice(DockerWebServiceApi[OpenVoiceSettings, OpenVoiceController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    def generate(self, source: FileLike.Type, voice: str, source_voice: str|None = None) -> File:
        url = f"http://{self.address}/generate/{voice}"
        if source_voice is not None:
            url+='/'+source_voice
        with FileLike(source, self.cache_folder) as stream:
            reply = requests.post(url, files=(('file', stream),))
        if reply.status_code != 200:
            raise ValueError(f"{reply.status_code}\n{reply.text}")
        
        return File(self.current_job_id+'.output.wav', reply.content, File.Kind.Audio)

    def train(self, voice: str, files: Iterable[FileLike.Type]):
        folder = self.controller.resource_folder('voices',voice)
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder)
        for file in files:
            with open(folder/FileLike.get_name(file), 'wb') as stream:
                with FileLike(file, self.cache_folder) as data:
                    stream.write(data.read())
        reply = requests.post(self.endpoint(f'train/{voice}'), json=dict(voice=voice))
        if reply.status_code!=200:
            raise ValueError(f'Endpoint train raised for voice {voice}\n{reply.text}')
        return "OK"


    Settings = OpenVoiceSettings
    Controller = OpenVoiceController

    
