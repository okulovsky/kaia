import requests
from kaia.infra import FileIO, MarshallingEndpoint
from pathlib import Path
from ...core import IApiDecider, File

class TortoiseTTS(IApiDecider):
    def __init__(self, address: str, outputs_folder: Path):
        MarshallingEndpoint.check_address(address)
        self.address = address
        self.outputs_folder = outputs_folder

    def dub(self, text: str, voice: str, count = 3):
        result = requests.post(f'http://{self.address}/dub', json=dict(output_file_name = self.current_job_id, text=text, voice=voice, count=count))
        if result.status_code == 500:
            raise ValueError(f"TortoiseTTS server returned {result.status_code}\n{result.text}")
        files = []
        for i, result in enumerate(result.json()):
            files.append(File(
                self.current_job_id+f'.output.{i}.wav',
                FileIO.read_bytes(self.outputs_folder/result),
                File.Kind.Audio
            ))
        return files