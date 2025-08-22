import argparse
from avatar.server import AvatarServerSettings, MessagingComponent, AvatarServer
from avatar.server.components import MainComponent, FileCacheComponent, StaticPathsComponent, TypeScriptComponent, AudioChunksComponent
from avatar.daemon import InitializationEvent
from yo_fluq import FileIO
from pathlib import Path
from phonix.components import PhonixMonitoringComponent
import phonix.daemon


if __name__ == '__main__':
    components = [
        MessagingComponent(
            aliases=MessagingComponent.create_aliases("avatar.messaging", "avatar.daemon", "phonix.daemon"),
            session_to_initialization_messages=dict(
                default=(InitializationEvent(),),
            )
        ),
        FileCacheComponent(Path("/cache")),
        MainComponent(FileIO.read_text('/index/index.html')),
        StaticPathsComponent(dict(static=Path('/static/'), scripts=Path('/scripts/'))),
        AudioChunksComponent(Path('/cache')),
        PhonixMonitoringComponent(Path('/cache'))
    ]
    settings = AvatarServerSettings(
        tuple(components),
    )
    server = AvatarServer(settings)
    server()


