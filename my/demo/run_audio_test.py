from kaia.kaia.audio_control.tools import *
from my.demo.audio_control import create_release_control_settings
from kaia.brainbox.deciders import docker_based as deciders

if __name__ == '__main__':
    rhasspy_api = deciders.RhasspyInstaller(deciders.RhasspySettings()).run_in_any_case_and_return_api()
    whisper_api: deciders.WhisperAPI = deciders.WhisperInstaller(
        deciders.WhisperSettings()).run_in_any_case_and_return_api()
    whisper_api.load_model('base')
    settings = create_release_control_settings(rhasspy_api, whisper_api)
    #VolumeTest(settings, [0.1, 0.3, 0.5])()
    #EchoTest(settings)()
    #PipelineTest(settings, 10)()
    #SilenceTest(settings)()
    ServerTest(settings)()


