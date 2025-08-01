from .app import KaiaApp, IAppInitializer
from avatar.messaging import IMessage
from avatar.server import AvatarServer, AvatarServerSettings, MessagingComponent, AvatarStream, AvatarApi
from avatar.server.components import *
from phonix.daemon import RecordingComponent
from dataclasses import dataclass, field
import importlib
import inspect
import pkgutil
from pathlib import Path
from copy import copy
from yo_fluq import FileIO


def find_subclasses_in_package(base_class: type, package_name: str) -> list[type]:
    subclasses = []
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue  # Пропускаем модули, которые не удаётся импортировать
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, base_class) and obj is not base_class:
                subclasses.append(obj)
    return subclasses

def create_aliases():
    all_subclasses = []
    for pkg in ["avatar.messaging", "avatar.services", "kaia"]:
        all_subclasses.extend(find_subclasses_in_package(IMessage, pkg))
    return {c.__name__: c for c in all_subclasses}



@dataclass
class AvatarServerAppSettings(IAppInitializer):
    additional_static_folders: dict[str, Path] = field(default_factory=dict)
    compile_scripts: bool = False
    add_chunks_component: bool = False
    add_phonix_component: bool = True


    def bind_app(self, app: 'KaiaApp'):
        bbox_folder = app.working_folder/'brainbox/temp/brainbox_cache'
        components = [
            MessagingComponent(app.working_folder/'avatar/messages.db', create_aliases()),
            FileCacheComponent(bbox_folder)
        ]
        static_folders = copy(self.additional_static_folders)
        web_folder = Path(__file__).parent.parent/'web'
        static_folders['static'] = web_folder/'static'
        components.append(StaticPathsComponent(static_folders))
        components.append(TypeScriptComponent(web_folder/'scripts', self.compile_scripts))
        components.append(IndexComponent(
            FileIO.read_text(web_folder / 'index.html'),
            f'127.0.0.1:13002'
        ))

        if self.add_phonix_component:
            components.append(RecordingComponent(bbox_folder))
        if self.add_chunks_component:
            components.append(AudioChunksComponent(bbox_folder))
            
        settings = AvatarServerSettings(
            tuple(components),
        )
        app.avatar_server = AvatarServer(settings)
        app.avatar_api = AvatarApi(f'127.0.0.1:{settings.port}')
        app.avatar_stream = AvatarStream(app.avatar_api)





