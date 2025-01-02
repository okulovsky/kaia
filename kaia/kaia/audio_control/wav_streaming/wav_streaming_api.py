from brainbox.framework.common import Fork, ApiUtils
from .wav_streaming_server import WavServerSettings, WavStreamingServer
from .wav_streaming_request import WavStreamingRequest
from dataclasses import dataclass
import requests
from pathlib import Path

@dataclass
class WavApiSettings:
    sample_rate: int = 16000
    frame_length: int = 512
    address: None|str = '127.0.0.1:13000'



class WavStreamingApi:
    def __init__(self, settings: WavApiSettings):
        self.settings = settings

    def wait(self):
        ApiUtils.wait_for_reply(f'http://{self.settings.address}', 5)


    def create_request(self, file_name: str, initial_buffer: list[list[int]]):
        request =  WavStreamingRequest(
            self.settings.address,
            file_name,
            self.settings.sample_rate,
            self.settings.frame_length,
            initial_buffer
        )
        return request

    def download(self, file_name: str):
        response = requests.get(f'http://{self.settings.address}/download/{file_name}')
        if response.status_code!=200:
            raise ValueError(response.text)
        return response.content

    @staticmethod
    def get_file_framerate(input_file_name):
        import wave
        with open(input_file_name,'rb') as file:
            with wave.open(file, "rb") as wave_file:
                return wave_file.getframerate()




    def send_file_right_away_and_return_sent_bytes(self, input_file_name: Path, target_file_id: str):
        from ..inputs import FakeInput

        input = FakeInput()
        input.set_sample(input_file_name)
        input.start()

        request = self.create_request(target_file_id, [])
        packages = []
        while not input.is_buffer_empty():
            data = input.read()
            packages.append(data)
            request.add_wav_data(data)

        request.send()
        return packages



    class Test:
        def __init__(self, api_settings: WavApiSettings, server_settings: WavServerSettings):
            self.api_settings = api_settings
            self.server_settings = server_settings

        def __enter__(self):
            service = WavStreamingServer(
                self.server_settings
            )
            self.fork = Fork(service).start()

            api = WavStreamingApi(self.api_settings)
            api.wait()
            return api

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.fork.terminate()

