from typing import *
import subprocess

class ContainerPusher:

    def get_auth_command(self) -> Iterable[str]:
        raise NotImplementedError()

    def get_remote_name(self, image_name: str, image_tag: str) -> str:
        raise NotImplementedError()

    def push(self, image_name: str, image_tag: str):
        raise NotImplementedError()
