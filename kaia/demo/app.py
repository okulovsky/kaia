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


    def get_fork_app(self, main_as_background: bool = False):
        services = []
        if self.brainbox_server is not None:
            services.append(self.brainbox_server)
        if self.avatar_server is not None:
            services.append(self.avatar_server)
        if self.kaia_server is not None:
            services.append(self.kaia_server)
        if self.audio_control_server is not None:
            services.append(self.audio_control_server)
        if self.wav_streaming_server is not None:
            services.append(self.wav_streaming_server)
        main = None
        if self.kaia_core is not None:
            if main_as_background:
                services.append(self.kaia_core)
            else:
                main = self.kaia_core
        return ForkApp(main, tuple(services))







