from kaia.kaia import audio_control as ac
from dataclasses import dataclass
import requests
from .app import KaiaApp

@dataclass
class MicSettings:
    mic_device_index: int = -1
    sample_rate: int = 16000
    silence_level: int = 200


class ApiCallback:
    def __init__(self, server_address: str, session_id: str):
        self.server_address = server_address
        self.session_id = session_id

    def __call__(self, filename: str):
        requests.post(
            f'http://{self.server_address}/command/{self.session_id}/command_audio',
            json=filename
        )

def create_settings(
        wav_streaming_address: str,
        mic_settings: MicSettings|None = None
):
    settings = ac.AudioControlSettings(
        wav_streaming_address = wav_streaming_address,
        mic_device_index=-1,
        sample_rate=16000,
        frame_length=512,
        silence_level=200,
        environment=ac.AudioControlSettings.Environments.PyAudio,
    )

    if mic_settings is not None:
        settings.mic_device_index = mic_settings.mic_device_index
        settings.sample_rate = mic_settings.sample_rate
        settings.silence_level = mic_settings.silence_level

    return settings


def set_audio_control_service_and_api(
        app: KaiaApp,
        mic_settings: MicSettings|None = None,
):
    settings = create_settings(
        app.wav_streaming_api.settings.address,
        mic_settings
    )

    settings.api_call_on_produced_file = ApiCallback(f'127.0.0.1:{app.kaia_server.settings.port}', app.session_id)

    app.audio_control_server = ac.AudioControlServer(ac.AudioControlService(settings.create_audio_control), settings.port)
    app.audio_control_api = ac.AudioControlApi(f'127.0.0.1:{settings.port}')

