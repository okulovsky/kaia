from .app import KaiaApp, IAppInitializer
from avatar.daemon.common import ServerStartedEvent
from avatar.app import AvatarServer, AvatarServerSettings, AvatarApi
from dataclasses import dataclass, field
from pathlib import Path
from foundation_kaia.misc import Loc


@dataclass
class AvatarServerAppSettings(IAppInitializer):
    additional_static_folders: dict[str, Path] = field(default_factory=dict)
    hide_logs: bool = True
    custom_frontend_folder: Path|None = None
    custom_html: str|None = None
    port: int = 13002


    def bind_app(self, app: 'KaiaApp'):
        if app.brainbox_cache_folder is None:
            raise ValueError("KaiaApp.brainbox_cache_folder must be set before AvatarServerAppSettings.bind_app")
        if app.avatar_resources_folder is None:
            raise ValueError("KaiaApp.avatar_resources_folder must be set before AvatarServerAppSettings.bind_app")

        start_message = ServerStartedEvent()

        settings = AvatarServerSettings(
            port = self.port,
            hide_logs=self.hide_logs,
            aliases_discovery_namespaces = ("avatar.messaging", "avatar.daemon", "kaia"),
            messages_ttl_in_seconds=60*60*2,
            cache_folder=app.brainbox_cache_folder,
            web_folder=Loc.root_folder/'kaia/web',
            frontend_folder=app.working_folder/'avatar/frontend' if self.custom_frontend_folder is None else self.custom_frontend_folder,
            resources_folder=app.avatar_resources_folder,
            custom_html=self.custom_html,
            starting_messages=dict(default=(start_message,)),
            additional_web_static_folders=self.additional_static_folders
        )

        app.avatar_api = AvatarApi(f'http://127.0.0.1:{self.port}')
        app._avatar_client = app.avatar_api.create_client()
        app.avatar_server = AvatarServer(settings)












