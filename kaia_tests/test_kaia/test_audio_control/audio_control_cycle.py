from kaia.brainbox.deciders.docker_based import (
    RhasspyInstaller, RhasspySettings,
    WhisperSettings, WhisperInstaller
)
from kaia.kaia.audio_control import setup as ac
from kaia.avatar.dub.core import Template


def get_intents():
    return [
        Template('Are you here?').with_name('ping'),
        Template('Repeat after me!').with_name('echo')
    ]

def create_audio_control_settings():
    rhasspy_installer = RhasspyInstaller(RhasspySettings())
    whisper_installer = WhisperInstaller(WhisperSettings())
    rhasspy_installer.install_if_not_installed()
    rhasspy_installer.server_endpoint.run()
    whisper_installer.install_if_not_installed()
    whisper_installer.server_endpoint.run()

    mic_data = ac.MicData(16000, 512)
    whisper_installer.create_api().load_model('base')

    rhasspy_api =  rhasspy_installer.create_api()
    whisper_api = whisper_installer.create_api()
    settings = ac.AudioControlSettings(
        mic_data,
        silence_margin_in_seconds=0.1,
        pause_between_iterations_in_seconds=0,
        rhasspy_api = rhasspy_api,
        whisper_api = whisper_api,
        silence_level=400,
        environment=ac.AudioControlSettings.Environments.Test,
        add_debug_output=True
    )
    return settings


