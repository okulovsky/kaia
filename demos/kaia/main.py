from typing import *
from kaia.brainbox import deciders
from .audio_control import create_audio_control_service_and_api
from .brainbox import create_brainbox_service_and_api
from .avatar import create_avatar_service_and_api
from .wav_streaming import create_wav_streaming_service_and_api_address
from .kaia_gui_service import create_gui_service_and_api, KaiaGuiApi
from .kaia_core_service import DemoCoreService, KaiaCoreAudioControlServiceSettings
from kaia.infra.app import KaiaApp
from pathlib import Path
from dataclasses import dataclass
from kaia.kaia.audio_control import AudioControlAPI
from kaia.brainbox import BrainBoxApi


@dataclass
class DemoApp:
    app: KaiaApp
    audio_api: AudioControlAPI
    gui_api: KaiaGuiApi
    brainbox_api: BrainBoxApi


def create_app(
        mic_samples_to_play: Optional[Iterable[Path]] = None,
        set_primary_service = True
    ):
    _ = deciders.RhasspyKaldiInstaller(deciders.RhasspyKaldiSettings()).run_in_any_case_and_create_api()
    whisper_api: deciders.WhisperExtendedAPI = deciders.WhisperInstaller(deciders.WhisperSettings()).run_in_any_case_and_create_api()
    whisper_api.load_model('base')
    _ = deciders.OpenTTSInstaller(deciders.OpenTTSSettings()).run_in_any_case_and_create_api()

    brain_box_service, brain_box_api, cache_path = create_brainbox_service_and_api()
    wav_streaming_service, wav_streaming_address = create_wav_streaming_service_and_api_address(cache_path)
    avatar_service, avatar_api = create_avatar_service_and_api(brain_box_api)
    audio_control_service, audio_control_api = create_audio_control_service_and_api(wav_streaming_address, mic_samples_to_play)
    gui_service, gui_api = create_gui_service_and_api()

    settings = KaiaCoreAudioControlServiceSettings(
        avatar_api=avatar_api,
        kaia_api=gui_api,
        audio_api=audio_control_api,
        brainbox_api=brain_box_api,
    )
    core_service = DemoCoreService(settings)

    app = KaiaApp()
    app.add_subproc_service(brain_box_service)
    app.add_subproc_service(avatar_service)
    app.add_subproc_service(wav_streaming_service)
    app.add_subproc_service(audio_control_service)
    app.add_subproc_service(gui_service)
    if set_primary_service:
        app.set_primary_service(core_service)
    else:
        app.add_subproc_service(core_service)

    return DemoApp(app, audio_control_api, gui_api, brain_box_api)







