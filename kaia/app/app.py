from dataclasses import dataclass
from pathlib import Path
from avatar.messaging import AvatarDaemon, AvatarClient
from avatar.app import AvatarServer, AvatarApi
from brainbox.framework import BrainBoxServer, BrainBoxApi
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
    brainbox_cache_folder: Path|None = None

    avatar_resources_folder: Path | None = None
    avatar_api: AvatarApi|None = None
    avatar_server: AvatarServer|None = None
    avatar_processor: AvatarDaemon|None = None

    _avatar_client: AvatarClient|None = None
    avatar_reporting_client: AvatarClient|None = None

    def create_avatar_client(self) -> AvatarClient|None:
        if self._avatar_client is None:
            raise ValueError()
        return self._avatar_client.clone_client()

    kaia_driver: KaiaDriver|None = None

    _MISSING = object()

    def get_fork_app(self, custom_main_service=_MISSING):
        if custom_main_service is KaiaApp._MISSING:
            custom_main_service = self.kaia_driver

        candidates = [
            self.brainbox_server,
            self.avatar_server,
            self.avatar_processor,
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


