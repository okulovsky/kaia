import os
from pathlib import Path
import requests
from ....framework import DockerWebServiceApi, FileLike, File, FileIO
from .settings import ResembleEnhanceSettings
from .controller import ResembleEnhanceController
from uuid import uuid4

class ResembleEnhance(DockerWebServiceApi[ResembleEnhanceSettings, ResembleEnhanceController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    def _process(self, file: FileLike.Type):
        uploads = self.controller.resource_folder('uploads')
        os.makedirs(uploads, exist_ok=True)
        for old_file in os.listdir(uploads):
            os.unlink(uploads/old_file)
        fname = str(uuid4())+'.wav'
        with FileLike(file, self.cache_folder) as stream:
            data = stream.read()
            with open(uploads/fname, 'wb') as out_stream:
                out_stream.write(data)
        reply = requests.post(f'http://{self.address}/enhance', json=dict(filename=fname))
        if reply.status_code != 200:
            raise ValueError(f"Decider returned code {reply.status_code}\n{reply.text}")
        js = reply.json()
        return js

    def process(self, file: FileLike.Type):
        return [
            File(name, FileIO.read_bytes(self.controller.resource_folder('outputs')/name))
            for name in self._process(file)
        ]

    def enhance(self, file: FileLike.Type):
        name = self._process(file)[-1]
        return File(name, FileIO.read_bytes(self.controller.resource_folder('outputs')/name))





    Settings = ResembleEnhanceSettings
    Controller = ResembleEnhanceController