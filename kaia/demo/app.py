from brainbox import BrainBoxApi, BrainBoxServer
from kaia.avatar import AvatarApi, AvatarServer
from kaia.kaia import KaiaServer, KaiaApi, KaiaCoreService
from kaia.kaia.audio_control import AudioControlServer, AudioControlApi
from kaia.kaia.audio_control.wav_streaming import WavStreamingServer, WavStreamingApi
from typing import Callable, Tuple, Optional
from brainbox.framework.common import Fork
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ForkApp:
    main: Optional[Callable] = None
    supporting: Tuple[Callable,...] = ()
    _forks = []

    def run(self):
        for service in self.supporting:
            self._forks.append(Fork(service).start())
        if self.main is not None:
            self.main()

    def terminate(self):
        for fork in self._forks:
            fork.terminate()


@dataclass
class KaiaApp:
    folder: Path
    session_id: str|None = 'demo'
    brainbox_server: BrainBoxServer|None = None
    brainbox_api: BrainBoxApi|None = None
    avatar_server: AvatarServer|None = None
    avatar_api: AvatarApi|None = None
    kaia_server: KaiaServer|None = None
    kaia_api: KaiaApi|None = None
    audio_control_server: AudioControlServer|None = None
    audio_control_api: AudioControlApi|None = None
    wav_streaming_server: WavStreamingServer|None = None
    wav_streaming_api: WavStreamingApi|None = None
    kaia_core: KaiaCoreService | None = None

    brainbox_cache_folder: Path|None = None

    _MISSING = object()

    def get_fork_app(self, custom_main_service = _MISSING):
        if custom_main_service is KaiaApp._MISSING:
            custom_main_service = self.kaia_core

        candidates = [
            self.brainbox_server,
            self.avatar_server,
            self.kaia_server,
            self.audio_control_server,
            self.wav_streaming_server,
            self.kaia_core
            ]

        main = None
        services = []
        for c in candidates:
            if c is None:
                continue
            if c == custom_main_service:
                main = c
            else:
                services.append(c)

        return ForkApp(main, tuple(services))







