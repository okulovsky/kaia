from typing import *
from .container_pusher import IContainerPusher

class ExistingRemoteContainerPusher(IContainerPusher):
    def __init__(self, image_name):
        self.image_name = image_name

    def get_push_command(self, local_image_name: str) -> Iterable[str|list[str]]:
        return []

    def get_auth_command(self):
        return []

    def get_remote_name(self) -> str:
        return self.image_name

    def get_ancestor(self) -> str:
        return self.image_name


class ExistingLocalContainerPusher(ExistingRemoteContainerPusher):
    def get_pull_command(self) -> Iterable[str|list[str]]:
        return []
