from dataclasses import dataclass
from pathlib import Path
from avatar.messaging import Stream, AvatarProcessor
from avatar.server import AvatarServer, AvatarApi
from brainbox import BrainBoxServer, BrainBoxApi
from phonix.server import PhonixServer
from kaia import KaiaDriver
from foundation_kaia.fork import ForkApp
from abc import abstractmethod, ABC

class IAppInitializer(ABC):
    @abstractmethod
    def bind_app(self, app: 'KaiaApp'):
        pass

@dataclass
class KaiaApp:
    working_folder: Path
    session_id: str = 'default'


    brainbox_server: BrainBoxServer|None = None
    brainbox_api: BrainBoxApi|None = None

    avatar_api: AvatarApi|None = None
    avatar_stream: Stream|None = None
    avatar_server: AvatarServer|None = None
    avatar_processor: AvatarProcessor|None = None

    phonix_server: PhonixServer|None = None

    kaia_driver: KaiaDriver|None = None

    _MISSING = object()

    def get_fork_app(self, custom_main_service=_MISSING):
        if custom_main_service is KaiaApp._MISSING:
            custom_main_service = self.kaia_driver

        candidates = [
            self.brainbox_server,
            self.avatar_server,
            self.avatar_processor,
            self.phonix_server,
            self.kaia_driver,
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


