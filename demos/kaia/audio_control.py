from kaia.kaia import audio_control as ac


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


def create_audio_control_service_and_api(wav_streaming_address, samples):
    if samples is None:
        settings = create_release_control_settings(wav_streaming_address)
    else:
        settings = create_test_control_settings(wav_streaming_address, samples)
    server = ac.AudioControlServer(settings.create_audio_control, settings.port)
    return server, ac.AudioControlAPI(f'127.0.0.1:{settings.port}')