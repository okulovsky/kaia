from kaia.brainbox import BrainBoxTestApi
from kaia.brainbox import deciders
from kaia.kaia.audio_control.audio_control_cycle import AudioControlSettings
from kaia.dub.core import Template, TemplatesCollection

class TestIntents(TemplatesCollection):
    ping = Template('Are you here?')
    echo = Template('Repeat after me!')


def create_brainbox_test_api(cache_folder = None):
    deciders.RhasspyInstaller(deciders.RhasspySettings()).run_in_any_case_and_create_api()
    deciders.WhisperInstaller(deciders.WhisperSettings()).run_in_any_case_and_create_api()
    return BrainBoxTestApi(
        {
            'Rhasspy': deciders.RhasspyInstaller(deciders.RhasspySettings()),
            'Whisper': deciders.WhisperInstaller(deciders.WhisperSettings()),
            'Collector': deciders.Collector(),
        },
        always_on_planner = True,
        cache_folder=cache_folder
    )


def create_audio_control_settings(wav_api=None):
    from demos.kaia.audio_control import create_test_control_settings
    settings = create_test_control_settings(wav_api, [])
    return settings
