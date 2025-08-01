from .component import RecordingComponent
from avatar.server.components import FileCacheComponent
from foundation_kaia.marshalling import TestApi
from avatar.server import AvatarApi, AvatarServerSettings, AvatarServer
from .recording_request import RecordingRequest
from dataclasses import dataclass

class RecordingApi(AvatarApi):
    def __init__(self, address: str):
        super().__init__(address)

    def create_recording_request(self, file_name: str, sample_rate: int, initial_buffer: list[int]):
        request =  RecordingRequest(
            self.address,
            file_name,
            sample_rate,
            initial_buffer
        )
        return request

    @staticmethod
    def get_file_framerate(input_file_name):
        import wave
        with open(input_file_name,'rb') as file:
            with wave.open(file, "rb") as wave_file:
                return wave_file.getframerate()



    class Test(TestApi['RecordingApi']):
        def __init__(self, folder):
            settings = AvatarServerSettings((
                RecordingComponent(folder),
                FileCacheComponent(folder),
            ))
            super().__init__(lambda z: RecordingApi(z), AvatarServer(settings))
