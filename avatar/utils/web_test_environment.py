import contextlib
from dataclasses import dataclass
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from avatar.app import AvatarApi, AvatarServer, AvatarServerSettings
from avatar.messaging import AvatarClient
from foundation_kaia.marshalling_2 import TestApi
from foundation_kaia.misc import Loc

_DEFAULT_SCRIPTS_FOLDER = Loc.root_folder / 'avatar' / 'web' / 'frontend'


@dataclass
class WebTestEnvironment:
    api: AvatarApi
    client: AvatarClient
    driver: webdriver.Chrome

    def print_console_logs(self):
        for entry in self.driver.get_log('browser'):
            print(f"[{entry['level']}] {entry['message']}")


class FrontendTestEnvironmentFactory:
    def __init__(self, base_url: str, headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self._driver: webdriver.Chrome | None = None


    def __enter__(self) -> webdriver.Chrome:
        opts = Options()
        if self.headless:
            opts.add_argument('--headless')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--autoplay-policy=no-user-gesture-required')
        opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        self._driver = webdriver.Chrome(options=opts)
        self._driver.get(self.base_url)
        return self._driver

    def __exit__(self, exc_type, exc, tb):
        if self._driver is not None:
            self._driver.quit()



class WebTestEnvironmentFactory:
    def __init__(
        self,
        html: str,
        scripts_folder: Path = _DEFAULT_SCRIPTS_FOLDER,
        headless: bool = True,
        port: int = 13002,
        aliases: dict[str, type] | None = None,
        aliases_discovery_namespaces: tuple[str, ...] = ('avatar',),
    ):
        self.html = html
        self.scripts_folder = scripts_folder
        self.headless = headless
        self.port = port
        self.aliases = aliases
        self.aliases_discovery_namespaces = aliases_discovery_namespaces
        self._stack = contextlib.ExitStack()
        self._env: WebTestEnvironment | None = None

    def __enter__(self) -> WebTestEnvironment:
        import tempfile
        cache_dir = self._stack.enter_context(tempfile.TemporaryDirectory())

        settings = AvatarServerSettings(
            port=self.port,
            custom_html=self.html,
            frontend_folder=self.scripts_folder,
            custom_aliases=self.aliases,
            aliases_discovery_namespaces=self.aliases_discovery_namespaces,
            cache_folder=Path(cache_dir),
        )

        api: AvatarApi = self._stack.enter_context(
            TestApi(AvatarApi, AvatarServer(settings))
        )
        client = api.create_client()

        driver = self._stack.enter_context(FrontendTestEnvironmentFactory(api.base_url, self.headless))

        self._env = WebTestEnvironment(api=api, client=client, driver=driver)
        return self._env

    def __exit__(self, exc_type, exc, tb):
        if self._env is not None:
            self._env.print_console_logs()
        return self._stack.__exit__(exc_type, exc, tb)


