import requests
from ....framework import DockerWebServiceApi, File
from .controller import OpenVoiceController
from .settings import OpenVoiceSettings


class OpenVoice(DockerWebServiceApi[OpenVoiceSettings, OpenVoiceController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    #TODO: inefficient. Should upload & train reference speaker as a separate endpoing, alike to Resemblyzer.
    #Also, should allow to upload several files, and glue them together inside the container
    def generate(self, source_speaker_path: str, reference_speaker_path: str) -> File:
       
        url = f"http://{self.address}/generate"

        with open(source_speaker_path, "rb") as source_file, \
        open(reference_speaker_path, "rb") as reference_file:
            files = {
                "source_speaker": source_file,
                "reference_speaker": reference_file,
            }
            reply = requests.post(url, files=files, timeout=30)

        if reply.status_code != 200:
            raise ValueError(f"{reply.status_code}\n{reply.text}")
        
        return File("cloned_output.wav", reply.content, File.Kind.Audio)

    Settings = OpenVoiceSettings
    Controller = OpenVoiceController

    
