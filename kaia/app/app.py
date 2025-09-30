from dataclasses import dataclass
from pathlib import Path
from avatar.messaging import AvatarDaemon, StreamClient, IStreamClient
from avatar.server import AvatarServer, AvatarApi
from brainbox import BrainBoxServer, BrainBoxApi
from phonix.components import PhonixApi
from kaia import KaiaDriver
from foundation_kaia.fork import ForkApp
from abc import abstractmethod, ABC
from phonix.daemon import PhonixDeamon

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
    custom_brainbox_cache_folder: Path|None = None

    @property
    def brainbox_cache_folder(self) -> Path:
        if self.custom_brainbox_cache_folder is not None:
            return self.custom_brainbox_cache_folder
        return self.working_folder/'cache'

    custom_avatar_resources_folder: Path | None = None

    @property
    def avatar_resources_folder(self) -> Path:
        if self.custom_avatar_resources_folder is not None:
            return self.custom_avatar_resources_folder
        return self.working_folder/'avatar-resources'

    avatar_api: AvatarApi|None = None
    avatar_server: AvatarServer|None = None
    avatar_processor: AvatarDaemon|None = None

    _avatar_client: StreamClient|None = None
    avatar_reporting_client: IStreamClient|None = None



    def create_avatar_client(self) -> StreamClient|None:
        if self._avatar_client is None:
            return None
        return self._avatar_client.clone()


    phonix_api: PhonixApi|None = None

    kaia_driver: KaiaDriver|None = None
    phonix_daemon: PhonixDeamon|None = None


    _MISSING = object()

    def get_fork_app(self, custom_main_service=_MISSING):
        if custom_main_service is KaiaApp._MISSING:
            custom_main_service = self.kaia_driver

        candidates = [
            self.brainbox_server,
            self.avatar_server,
            self.avatar_processor,
            self.phonix_daemon,
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


