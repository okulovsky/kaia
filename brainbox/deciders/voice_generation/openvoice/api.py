import requests
from ...core import IApiDecider, File


class OpenVoice(IApiDecider):  
    def __init__(self, address: str):
        self.address = address

    def generate(self,
                  source_speaker_path: str,
                  reference_speaker_path: str) -> File:
       
        url = f"http://{self.address}/synthesize"

        files = {
            "source_speaker": open(source_speaker_path, "rb"),
            "reference_speaker": open(reference_speaker_path, "rb"),
        }
        reply = requests.post(url, json=files, timeout=30)
        if reply.status_code != 200:
            raise ValueError(f"{reply.status_code}\n{reply.text}")
        
        return File("cloned_output.wav", reply.content, File.Kind.Audio)

    

    
