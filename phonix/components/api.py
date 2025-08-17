from .recording import PhonixRecordingComponent, RecordingRequest
from .monitoring import PhonixMonitoringComponent
from avatar.server.components import FileCacheComponent
from foundation_kaia.marshalling import TestApi
from avatar.server import AvatarApi, AvatarServerSettings, AvatarServer, MessagingComponent
import requests


class PhonixApi(AvatarApi):
    def __init__(self, address: str):
        super().__init__(address)

    def create_recording_request(self, file_name: str, sample_rate: int, initial_buffer: list[int]):
        request = RecordingRequest(
            self.address,
            file_name,
            sample_rate,
            initial_buffer
        )
        return request


    def get_snapshot(self):
        reply = requests.get(f'http://{self.address}/phonix-monitor/screenshot')
        reply.raise_for_status()
        return reply.content

    def init_monitor(self):
        reply = requests.post(f'http://{self.address}/phonix-monitor/init')
        reply.raise_for_status()

    @staticmethod
    def get_file_framerate(input_file_name):
        import wave
        with open(input_file_name, 'rb') as file:
            with wave.open(file, "rb") as wave_file:
                return wave_file.getframerate()

    class Test(TestApi['PhonixApi']):
        def __init__(self, folder):
            settings = AvatarServerSettings((
                PhonixRecordingComponent(folder),
                PhonixMonitoringComponent(folder),
                FileCacheComponent(folder),
                MessagingComponent()
            ))
            super().__init__(lambda z: PhonixApi(z), AvatarServer(settings))
