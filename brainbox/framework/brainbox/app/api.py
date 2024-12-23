import uuid
from typing import Iterable, Union
from ...common.marshalling import Api, bind_to_api, TestApi
from ...common import File, Loc, FileLike, IDecider, LocHolder
from .interface import IBrainboxService
from .service import BrainBoxService
from .task import IBrainBoxTask
from ...controllers import IController, ControllerRegistry, ControllerApi
import os
import requests
from .server import BrainBoxServer, BrainBoxServiceSettings
from pathlib import Path
from .serverless_test import ServerlessTest


@bind_to_api(BrainBoxService)
class BrainBoxApi(Api, IBrainboxService):
    def __init__(self,
                 address: str = '127.0.0.1:8090',
                 cache_folder: Path|None = None
                 ):
        super().__init__(address)
        self.cache_folder = cache_folder if cache_folder is not None else Loc.cache_folder

    @property
    def controller_api(self) -> ControllerApi:
        return ControllerApi(self.address)

    def _process_download_arguments(
            self,
            fname: str|File,
            custom_file_path: Path|None = None,
            replace: bool = False) -> tuple[bool, str, Path]:
        if isinstance(fname, File):
            fname = fname.name
        if custom_file_path is None:
            custom_file_path = self.cache_folder/fname
        os.makedirs(custom_file_path.parent, exist_ok=True)
        should_download = True
        if custom_file_path.is_file():
            if not replace:
                should_download = False
        return should_download, fname, custom_file_path

    def _download_and_cache(self, fname: str, path: Path) -> bytes:
        address = f'http://{self.address}/cache/download/{fname}'
        response = requests.get(address)
        if response.status_code != 200:
            raise ValueError(f"Couldn't get file content for {address}\n" + response.text)
        content = response.content

        with open(path, 'wb') as stream:
            stream.write(content)
        return content


    def download(self, fname: str|File) -> File:
        should_download, fname, path = self._process_download_arguments(fname)
        if should_download:
            content = self._download_and_cache(fname, path)
            return File(fname, content)
        else:
            return File.read(path)

    def custom_download(self, fname: str|File, custom_file_path: Path|None = None, replace: bool = False) -> Path:
        should_download, fname, path = self._process_download_arguments(fname, custom_file_path, replace)
        if should_download:
            self._download_and_cache(fname, path)
        return path

    def upload(self, filename: str, data: FileLike.Type):
        with FileLike(data, None) as stream:
            reply = requests.post(
                f'http://{self.address}/cache/upload',
                files=(
                    (filename, stream),
                )
            )
        if reply.status_code != 200:
            raise ValueError(reply.text)


    class Test(TestApi['BrainBoxApi']):
        def __init__(self,
                     services: Iterable[Union[IDecider, IController]]|None = None,
                     run_controllers_in_default_environment: bool = True,
                     ):
            self.test_folder = Loc.create_test_folder('brainbox_test_runs')
            locator = LocHolder(self.test_folder.path)
            registry = ControllerRegistry.discover_or_create(services)
            if not run_controllers_in_default_environment:
                registry.locator = locator
            settings = BrainBoxServiceSettings(registry, locator = locator, debug_output=True)
            super().__init__(BrainBoxApi, BrainBoxServer(settings))

        def __enter__(self):
            self.test_folder.__enter__()
            self._api = super().__enter__()
            return self._api

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._api.shutdown()
            super().__exit__(exc_type, exc_val, exc_tb)
            self.test_folder.__exit__(exc_type, exc_val, exc_tb)


    ServerlessTest = ServerlessTest



