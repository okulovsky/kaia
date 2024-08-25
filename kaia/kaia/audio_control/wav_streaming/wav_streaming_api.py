from .wav_streaming_server import WavServerSettings, WavStreamingServer
from .wav_streaming_request import WavStreamingRequest
from dataclasses import dataclass
from kaia.infra.app import KaiaApp
import requests

@dataclass
class WavApiSettings:
    sample_rate: int = 16000
    frame_length: int = 512
    address: None|str = '127.0.0.1:13000'



class WavStreamingApi:
    def __init__(self, settings: WavApiSettings):
        self.settings = settings

    def create_request(self, file_name: str, initial_buffer: list[list[int]]):
        return WavStreamingRequest(
            self.settings.address,
            file_name,
            self.settings.sample_rate,
            self.settings.frame_length,
            initial_buffer
        )

    def download(self, file_name: str):
        response = requests.get(f'http://{self.settings.address}/download/{file_name}')
        if response.status_code!=200:
            raise ValueError(response.text)
        return response.content


class WavStreamingTestApi:
    def __init__(self, api_settings: WavApiSettings, server_settings: WavServerSettings):
        self.api_settings = api_settings
        self.server_settings = server_settings

    def __enter__(self):
        service = WavStreamingServer(
            self.server_settings
        )
        self.app = KaiaApp()
        self.app.add_subproc_service(service)
        self.app.run_services_only()

        api = WavStreamingApi(self.api_settings)
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.app.exit()
