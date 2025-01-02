from kaia.kaia import audio_control as ac

def create_test_settings(wav_api, action_on_produced_file):
    settings = ac.AudioControlSettings(
        mic_device_index=-1,
        sample_rate=22050,
        frame_length=512,
        silence_margin_in_seconds=0.1,
        pause_between_iterations_in_seconds=0.01,
        silence_level=1000,
        environment=ac.AudioControlSettings.Environments.Test,
        api_call_on_produced_file=action_on_produced_file
    )
    if wav_api is not None:
        settings.wav_streaming_address=wav_api.settings.address
    return settings

