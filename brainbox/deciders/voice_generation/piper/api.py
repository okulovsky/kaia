import requests
from typing import Optional
from .controller import PiperController
from .settings import PiperSettings
from .model import PiperModel
from ....framework import DockerWebServiceApi, File


class Piper(DockerWebServiceApi[PiperSettings, PiperController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    def voiceover(self,
                  text: str,
                  model: str = "en"
                  ) -> File:
       
        url = f"http://{self.address}/synthesize"
        payload = {
            "text": text,
            "model": model
        }
        reply = requests.post(url, json=payload, timeout=30)
        if reply.status_code != 200:
            raise ValueError(f"{reply.status_code}\n{reply.text}")
        
        return File(self.current_job_id+'.output.wav', reply.content, File.Kind.Audio)

    Controller = PiperController
    Settings = PiperSettings
    Model = PiperModel

    
