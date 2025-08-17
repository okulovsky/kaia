from .avatar_daemon_app_settings import AvatarDaemonAppSettings
from .avatar_server_app_settings import AvatarServerAppSettings
from .brainbox_app_settings import BrainboxAppSettings
from .kaia_driver_settings import KaiaDriverSettings
from .phonix_app_settings import PhonixAppSettings
from .app import KaiaApp
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class KaiaAppSettings:
    brainbox: BrainboxAppSettings|None = field(default_factory=BrainboxAppSettings)
    avatar_processor: AvatarDaemonAppSettings|None = field(default_factory=AvatarDaemonAppSettings)
    avatar_server: AvatarServerAppSettings|None = field(default_factory=AvatarServerAppSettings)
    kaia: KaiaDriverSettings|None = field(default_factory=KaiaDriverSettings)
    phonix: PhonixAppSettings|None = field(default_factory=PhonixAppSettings)


    def create_app(self, working_folder: Path):
        app = KaiaApp(working_folder)
        for s in [self.brainbox, self.avatar_server, self.avatar_processor, self.kaia, self.phonix]:
            if s is not None:
                s.bind_app(app)
        return app


