import os
from typing import *
from brainbox.framework.common.marshalling import Api, bind_to_api, TestApi
from brainbox.framework import Loc, Locator
from .interface import IControllerService
from .service import ControllerService, ControllerServerSettings
from .server import ControllerServer
from ...common import IDecider, File, FileLike
from ..controller import IController, ControllerRegistry
from pathlib import Path
import requests

@bind_to_api(ControllerService)
class ControllerApi(Api, IControllerService):
    def __init__(self, address: str):
        super().__init__(address)

    def download_resource(self,
                 decider: str|IDecider|IController|type[IDecider]|type[IController],
                 path: str,
                 target_path: Path|str
                 ):
        decider = ControllerRegistry.to_controller_name(decider)
        address = f'http://{self.address}/resources/download/{decider}/{path}'
        response = requests.get(address)
        if response.status_code != 200:
            raise ValueError(f"Couldn't get file content for {address}\n" + response.text)
        content = response.content
        os.makedirs(Path(target_path).parent, exist_ok=True)
        with open(target_path, 'wb') as stream:
            stream.write(content)


    def upload_resource(self,
               decider: str | IDecider | IController | type[IDecider] | type[IController],
               path: str,
               data: FileLike.Type
               ):
        decider = ControllerRegistry.to_controller_name(decider)
        with FileLike(data, None) as stream:
            reply = requests.post(
                f'http://{self.address}/resources/upload/{decider}/{path}',
                files=(
                    ('filename', stream),
                )
            )
        if reply.status_code != 200:
            raise ValueError(reply.text)

    def install_if_not_installed(self, decider: str|IDecider|IController|type[IDecider]|type[IController], with_self_test: bool = True):
        if not self.controller_status(decider).installation_status.installed:
            self.install(decider)
            if with_self_test:
                self.self_test(decider)


    class Test(TestApi['ControllerApi']):
        def __init__(self,
                     services: Iterable[IDecider|IController]|None = None,
                     custom_folder: Path|None = None
                     ):
            if custom_folder is not None:
                loc = Locator(custom_folder)
            else:
                loc = Loc
            registry = ControllerRegistry.discover_or_create(services)
            registry.locator = loc
            settings = ControllerServerSettings(registry)
            super().__init__(ControllerApi, ControllerServer(settings))
