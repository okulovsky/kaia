from kaia.app import KaiaAppSettings, KaiaApp
from avatar.daemon import *
from yo_fluq import Query
from pathlib import Path
from unittest import TestCase
from foundation_kaia.misc import Loc
from loguru import logger
import contextlib
from avatar.app import compile_frontend

class BackendTestEnvironment:
    def __init__(self, tc: TestCase, folder: Path, settings: KaiaAppSettings, app: KaiaApp, client: AvatarClient):
        self.tc = tc
        self.settings = settings
        self.folder = folder
        self.app = app
        self.client = client
        self.base_url = self.app.avatar_api.base_url
        self.silent_processing = False


    def _preview_message(self, iterable):
        def _():
            for message in iterable:
                if isinstance(message, SoundLevelReport):
                    continue
                if isinstance(message, ExceptionEvent):
                    print("*"*80)
                    print("Exception in the service")
                    print(message.source)
                    print(message.traceback)
                    exit(1)
                if not self.silent_processing:
                    logger.info(f"TEST SEES MESSAGE {message}")
                yield message

        return Query.en(_())


    def upload(self, file: Path):
        if not file.is_file():
            raise ValueError(f"File {file} does not exist")
        self.app.avatar_api.cache.upload(file.name, file)
        return file.name

    def say(self, file):
        self.client.push(SoundInjectionCommand(self.upload(file)))
        return self.client

    def wait_for(self, condition: Callable[[IMessage], bool]):
        for message in self.client.query(10).feed(self._preview_message):
            if condition(message):
                break

    def parse_reaction(self, expected_command: Type, response: list[IMessage]|None = None):
        msg = None
        for message in self.client.query(10).feed(self._preview_message):
            if response is not None:
                response.append(message)
            if isinstance(message, expected_command):
                if msg is None:
                    msg = message
                else:
                    raise ValueError("Only one message is expected")
            if msg is not None:
                if message.is_confirmation_of(msg):
                    return




class BackendTestEnvironmentFactory:
    def __init__(self, tc: TestCase, html: str|None = None):
        self.tc = tc
        self.html = html
        self._stack = contextlib.ExitStack()


    def __enter__(self) -> BackendTestEnvironment:
        folder = self._stack.enter_context(Loc.create_test_folder())

        settings = KaiaAppSettings()
        settings.custom_avatar_resources_folder = Loc.root_folder / 'kaia/app/files/avatar-resources'
        settings.avatar_server.custom_frontend_folder = Loc.data_folder/'demo/avatar/frontend'
        compile_frontend(settings.avatar_server.custom_frontend_folder)
        if self.html is not None:
            settings.avatar_server.custom_html = self.html
        else:
            settings.avatar_processor.mock_sound_service = True

        settings.avatar_processor.timer_event_span_in_seconds = None
        settings.avatar_processor.initialization_event_at_startup = False
        settings.brainbox.deciders_files_in_kaia_working_folder = False



        app = settings.create_app(folder)
        client = app.create_avatar_client()

        self._stack.enter_context(app.get_fork_app(None))

        app.avatar_api.wait_for_connection()

        return BackendTestEnvironment(self.tc, folder, settings, app, client)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._stack.__exit__(exc_type, exc_val, exc_tb)