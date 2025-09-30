from .app import KaiaApp, IAppInitializer
from avatar.messaging import IMessage
from avatar.server import AvatarServer, AvatarServerSettings, MessagingComponent, AvatarStream, AvatarApi
from avatar.server.components import *
from phonix.components import PhonixMonitoringComponent, PhonixRecordingComponent, PhonixApi
from dataclasses import dataclass, field
import importlib
import inspect
import pkgutil
from pathlib import Path
from copy import copy
from yo_fluq import FileIO


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

        components = [
            MessagingComponent(
                app.working_folder/'avatar/messages.db',
                MessagingComponent.create_aliases("avatar.messaging", "avatar.daemon", "kaia"),
                dict(default=(start_message,))
            ),
            FileCacheComponent(app.brainbox_cache_folder)
        ]
        static_folders = copy(self.additional_static_folders)
        web_folder = Path(__file__).parent.parent/'web'
        static_folders['static'] = web_folder/'static'
        components.append(StaticPathsComponent(static_folders))
        components.append(TypeScriptComponent(web_folder/'scripts', self.compile_scripts))
        components.append(MainComponent(FileIO.read_text(web_folder / 'index.html')))
        components.append(ResourcesComponent(app.avatar_resources_folder))

        if self.add_phonix_component:
            components.append(PhonixRecordingComponent(app.brainbox_cache_folder))
            components.append(PhonixMonitoringComponent(app.brainbox_cache_folder))
        if self.add_chunks_component:
            components.append(AudioChunksComponent(app.brainbox_cache_folder))
            
        settings = AvatarServerSettings(
            tuple(components),
            PORT,
            self.hide_logs
        )
        app.avatar_api = AvatarApi(f'127.0.0.1:{PORT}')
        app._avatar_client = AvatarStream(app.avatar_api).create_client(start_message_id)
        app.avatar_server = AvatarServer(settings)
        app.phonix_api = PhonixApi(f'127.0.0.1:{PORT}')










