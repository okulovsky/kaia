import os
import requests
from kaia.infra import FileIO, MarshallingEndpoint
from pathlib import Path

class TortoiseTTSApi:
    def __init__(self, address: str, outputs_folder: Path):
        MarshallingEndpoint.check_address(address)
        self.address = address
        self.outputs_folder = outputs_folder


    def dub_and_return_filenames(self, text, voice, count=3):
        result = requests.post(f'http://{self.address}/dub', json=dict(text=text, voice=voice, count=count))
        if result.status_code == 500:
            raise ValueError(f"TortoiseTTS server returned {result.status_code}\n{result.text}")
        return result.json()

    def dub_and_return_bytes(self, text, voice, count=3):
        files = self.dub_and_return_filenames(text, voice, count)
        contents = []
        for file in files:
            path = self.outputs_folder/file
            contents.append(FileIO.read_bytes(path))
            os.unlink(path)
        return contents

