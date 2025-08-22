import webbrowser
from avatar.server import AvatarServerSettings, AvatarApi, AvatarStream, MessagingComponent
from avatar.server.components import MainComponent, StaticPathsComponent, TypeScriptComponent, FileCacheComponent
from avatar.daemon import ChatCommand, ImageCommand, ButtonGridCommand, InitializationEvent
from kaia.app.avatar_server_app_settings import create_aliases
from pathlib import Path
from yo_fluq import FileIO
import time
from foundation_kaia.misc import Loc

if __name__ == '__main__':
    with Loc.create_test_folder() as cache_folder:
        with Loc.create_test_file() as db_path:
            settings = AvatarServerSettings(
                (
                    MainComponent(FileIO.read_text(Path(__file__).parent/'index.html')),
                    StaticPathsComponent(dict(static=Path(__file__).parent/'static')),
                    TypeScriptComponent(Path(__file__).parent/'scripts', True),
                    MessagingComponent(db_path, create_aliases()),
                    FileCacheComponent(cache_folder),
                ),
                hide_logs=True,

            )
            with AvatarApi.Test(settings) as api:
                client = AvatarStream(api).create_client()
                api.wait()
                webbrowser.open('http://'+api.address+'/main')
                for message in client.query():
                    print(message)
                    if isinstance(message, InitializationEvent):
                        img = api.file_cache.upload(FileIO.read_bytes(Path(__file__).parent / 'image.png'))
                        client.put(ImageCommand(img))
                        for element in ChatCommand.MessageType:
                            client.put(ChatCommand(element.name, element, element.name, '/static/unknown.png'))
                        client.put(ButtonGridCommand(elements=(
                            ButtonGridCommand.Button("Caption", 0, 0, column_span=4),
                            ButtonGridCommand.Button("Button 1", 1, 1, button_feedback='test 1'),
                            ButtonGridCommand.Button("Button 2", 2, 2, button_feedback='test 2'),
                        )))


