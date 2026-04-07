from .app import KaiaApp, IAppInitializer
from avatar.messaging import IMessage
from avatar.app import AvatarServer, AvatarServerSettings, AvatarApi
from avatar.daemon import TickEvent
from dataclasses import dataclass, field
from pathlib import Path
from foundation_kaia.misc import Loc


@dataclass
class ServerStartedEvent(IMessage):
    pass

@dataclass
class AvatarServerAppSettings(IAppInitializer):
    additional_static_folders: dict[str, Path] = field(default_factory=dict)
    hide_logs: bool = True
    custom_frontend_folder: Path|None = None
    custom_html: str|None = None


    def bind_app(self, app: 'KaiaApp'):
        PORT = 13002

        start_message = ServerStartedEvent()
        start_message_id = start_message.envelop.id

        settings = AvatarServerSettings(
            PORT,
            self.hide_logs,
            ("avatar.messaging", "avatar.daemon", "kaia"),
            60*60*2,
            app.brainbox_cache_folder,
            Loc.root_folder/'kaia/web',
            app.working_folder/'avatar/frontend' if self.custom_frontend_folder is None else self.custom_frontend_folder,
            Path(__file__).parent/'avatar-resources',
            custom_html=self.custom_html
        )

        app.avatar_api = AvatarApi(f'http://127.0.0.1:{PORT}')
        app._avatar_client = app.avatar_api.create_client()
        app._avatar_client.set_last_id(start_message_id)
        app.avatar_server = AvatarServer(settings)











