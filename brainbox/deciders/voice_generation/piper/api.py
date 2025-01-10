import requests
from typing import Optional
from ...core import IApiDecider, File


class Piper(IApiDecider):  
    def __init__(self, address: str):
        self.address = address

    def download_model(self, name: str, config_url: str, url: str):
        url_api = f"http://{self.address}/download_model"
        payload = {
            "name": name,
            "config_url": config_url,
            "url": url
        }
        reply = requests.post(url_api, json=payload, timeout=120)
        if reply.status_code != 200:
            raise ValueError(f"{reply.status_code}\n{reply.text}")
        return reply.json()
    
    def list_models(self):
        url = f"http://{self.address}/list_models"
        reply = requests.get(url, timeout=30)
        if reply.status_code != 200:
            raise ValueError(f"{reply.status_code}\n{reply.text}")
        return reply.json()

    def voiceover(self,
                  text: str,
                  model_path: str = "/config/en_GB-alba-medium.onnx"
                  ) -> File:
       
        url = f"http://{self.address}/synthesize"
        payload = {
            "text": text,
            "model_path": model_path
        }
        reply = requests.post(url, json=payload, timeout=30)
        if reply.status_code != 200:
            raise ValueError(f"{reply.status_code}\n{reply.text}")
        
        return File("piper_output.wav", reply.content, File.Kind.Audio)

    

    
