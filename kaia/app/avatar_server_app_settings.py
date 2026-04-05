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
    compile_scripts: bool = False
    add_chunks_component: bool = False
    add_phonix_component: bool = True
    hide_logs: bool = True


    def bind_app(self, app: 'KaiaApp'):
        PORT = 13002

        start_message = ServerStartedEvent()
        start_message_id = start_message.envelop.id

        settings = AvatarServerSettings(
            PORT,
            True,
            ("avatar.messaging", "avatar.daemon", "kaia"),
            60*60*2,
            app.brainbox_cache_folder,
            Loc.root_folder/'kaia/web',
            app.working_folder/'avatar/frontend',
            Path(__file__).parent/'avatar-resources',
        )

        app.avatar_api = AvatarApi(f'http://127.0.0.1:{PORT}')
        app._avatar_client = app.avatar_api.create_client().set_last_id(start_message_id)
        app.avatar_server = AvatarServer(settings)











