from kaia.kaia.audio_control.setup import AudioControlSettings, MicData
from kaia.kaia.audio_control import core as ac


def create_test_control_settings(rhasspy_api, whisper_api, samples):
    return AudioControlSettings(
        mic_device_index=-1,
        mic_data=MicData(sample_rate = 16000, frame_length = 512),
        silence_margin_in_seconds=0.01,
        pause_between_iterations_in_seconds=0,
        rhasspy_api = rhasspy_api,
        whisper_api = whisper_api,
        silence_level=400,
        environment=AudioControlSettings.Environments.Test,
        add_debug_output=True,
        load_mic_samples=samples,
    )



def create_release_control_settings(rhasspy_api, whisper_api):
    return AudioControlSettings(
        mic_data=MicData(16000, 512),
        rhasspy_api=rhasspy_api,
        whisper_api=whisper_api,
        environment=AudioControlSettings.Environments.PyAudio,
        silence_level=40,
    )


def create_audio_control_service_and_api(rhasspy_api, whisper_api, samples):
    if samples is None:
        settings = create_release_control_settings(rhasspy_api, whisper_api)
    else:
        settings = create_test_control_settings(rhasspy_api, whisper_api, samples)
    server = ac.AudioControlServer(settings.create_audio_control, settings.port)
    return server, ac.AudioControlAPI(f'127.0.0.1:{settings.port}')