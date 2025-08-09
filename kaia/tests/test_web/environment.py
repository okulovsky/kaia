import contextlib
from typing import Any
from dataclasses import dataclass
from foundation_kaia.misc import Loc
from avatar.messaging import StreamClient
from avatar.server import AvatarServerSettings, AvatarApi, MessagingComponent, AvatarStream
from avatar.server.components import TypeScriptComponent, MainComponent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from kaia.tests.helper import Helper, SeleniumDriver

@dataclass
class TestEnvironment:
    api: AvatarApi
    client: StreamClient
    driver: webdriver.Chrome


class TestEnvironmentFactory:
    def __init__(self,
                 html: str,
                 headless: bool = True,
                 aliases: dict[str,type]|None = None
                 ):
        self.html = html
        self.headless = headless
        self.aliases = aliases
        self._stack = contextlib.ExitStack()

    def __enter__(self) -> TestEnvironment:
        # 1) temp folder / DB
        db_path = self._stack.enter_context(Loc.create_test_file())

        # 2) static / TS / messaging components
        web_folder = Loc.root_folder / 'kaia' / 'web'
        assert web_folder.exists()

        PORT = 13002
        settings = AvatarServerSettings(
            (
                TypeScriptComponent(web_folder / 'scripts', True),
                MessagingComponent(db_path, self.aliases),
                MainComponent(self.html, f'127.0.0.1:{PORT}')
            ),
            PORT,
            False
        )

        # 3) AvatarApi.Test
        api = self._stack.enter_context(AvatarApi.Test(settings))
        client = AvatarStream(api).create_client()

        # 4) client
        driver = self._stack.enter_context(SeleniumDriver(api, self.headless))

        return TestEnvironment(
            api=api,
            client=client,
            driver=driver
        )

    def __exit__(self, exc_type, exc, tb):
        return self._stack.__exit__(exc_type, exc, tb)
