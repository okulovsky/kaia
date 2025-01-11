import requests
from ...core import IApiDecider, File


class OpenVoice(IApiDecider):  
    def __init__(self, address: str):
        self.address = address

    def generate(self,
                  source_speaker_path: str,
                  reference_speaker_path: str) -> File:
       
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

    

    
