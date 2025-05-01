import requests
from typing import Optional
from .controller import PiperController
from .settings import PiperSettings
from .model import PiperModel
from ....framework import DockerWebServiceApi, File, IPrerequisite, BrainBoxApi
from pathlib import Path


class Piper(DockerWebServiceApi[PiperSettings, PiperController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    def voiceover(self,
                  text: str,
                  model: str = "en",
                  speaker: int|None = None,
                  noise_scale: float|None = None,
                  length_scale: float|None = None,
                  noise_w: float|None = None,
                  ) -> File:
        url = f"http://{self.address}/synthesize"
        payload = {
            "text": text,
            "model": model,
            "noise_scale": noise_scale,
            "length_scale": length_scale,
            "noise_w": noise_w,
            "speaker": speaker
        }
        reply = requests.post(url, json=payload, timeout=30)
        if reply.status_code != 200:
            raise ValueError(f"{reply.status_code}\n{reply.text}")
        
        return File(self.current_job_id+'.output.wav', reply.content, File.Kind.Audio)

    Controller = PiperController
    Settings = PiperSettings
    Model = PiperModel


    class UploadVoice(IPrerequisite):
        def __init__(self,
                     onnx_file_location: Path,
                     custom_json_file_location: Path|None = None,
                     custom_name: str|None = None
                     ):
            self.onnx_file_location = onnx_file_location
            self.custom_json_file_location = custom_json_file_location
            self.custom_name = custom_name

        def execute(self, api: BrainBoxApi):
            name = self.custom_name
            if name is None:
                name = self.onnx_file_location.name.split('.')[0]

            api.controller_api.upload_resource(
                'Piper',
                f'models/{name}.onnx',
                self.onnx_file_location
            )
            json_location = self.custom_json_file_location
            if json_location is None:
                json_location = self.onnx_file_location.parent/(self.onnx_file_location.name+'.json')
            api.controller_api.upload_resource(
                'Piper',
                f'models/{name}.onnx.json',
                json_location
            )

    class DeleteVoice(IPrerequisite):
        def __init__(self, name: str):
            self.name = name

        def execute(self, api: BrainBoxApi):
            api.controller_api.delete_resource('Piper', f'models/{self.name}.onnx')
            api.controller_api.delete_resource('Piper', f'models/{self.name}.onnx.json')
