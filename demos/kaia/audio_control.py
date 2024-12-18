from kaia.kaia import audio_control as ac
from dataclasses import dataclass
import requests

@dataclass
class MicSettings:
    mic_device_index: int = -1
    sample_rate: int = 16000
    silence_level: int = 200



def create_test_control_settings(wav_streaming_address, samples):
    return ac.AudioControlSettings(
        wav_streaming_address = wav_streaming_address,
        mic_device_index=-1,
        load_mic_samples=samples,
        sample_rate=22050,
        frame_length=512,
        silence_margin_in_seconds=0.1,
        pause_between_iterations_in_seconds=0.01,
        silence_level=1000,
        environment=ac.AudioControlSettings.Environments.Test,
    )



def create_release_control_settings(wav_streaming_address):
    return ac.AudioControlSettings(
        wav_streaming_address = wav_streaming_address,
        mic_device_index=-1,
        sample_rate=16000,
        frame_length=512,
        silence_level=200,
        environment=ac.AudioControlSettings.Environments.PyAudio,
    )


class ApiCallback:
    def __init__(self, server_address: str, session_id: str):
        self.server_address = server_address
        self.session_id = session_id

    def __call__(self, filename: str):
        requests.post(
            f'http://{self.server_address}/command/{self.session_id}/command_audio',
            json=filename
        )


def create_audio_control_service_and_api(
        wav_streaming_address,
        samples,
        mic_settings: MicSettings|None = None,
        api_callback: ApiCallback|None = None
):
    if samples is None:
        settings = create_release_control_settings(wav_streaming_address)
        if mic_settings is not None:
            settings.mic_device_index = mic_settings.mic_device_index
            settings.sample_rate = mic_settings.sample_rate
            settings.silence_level = mic_settings.silence_level
    else:
        settings = create_test_control_settings(wav_streaming_address, samples)
    if api_callback is not None:
        settings.api_call_on_produced_file = api_callback
    server = ac.AudioControlServer(settings.create_audio_control, settings.port)
    return server, ac.AudioControlAPI(f'127.0.0.1:{settings.port}')