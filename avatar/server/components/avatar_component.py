from typing import Callable, Iterable
from abc import ABC, abstractmethod
import flask
from dataclasses import dataclass, field

@dataclass
class AvatarTocRecord:
    url: str
    title: str


class AvatarApp:
    def __init__(self, app: flask.Flask):
        self.app = app
        self.toc: list[AvatarTocRecord] = []

    def add_url_rule(self,
                     rule: str,
                     view_func: Callable,
                     methods: Iterable[str],
                     endpoint: str|None = None,
                     caption: str|None = None
                     ):
        self.app.add_url_rule(rule = rule, view_func=view_func, endpoint=endpoint, methods=methods)
        if caption is not None:
            self.add_link(rule, caption)

    def add_link(self, url: str, caption: str):
        if caption is not None:
            self.toc.append(AvatarTocRecord(url, caption))


class IAvatarComponent(ABC):
    App = AvatarApp

    @abstractmethod
    def setup_server(self, app: AvatarApp, address: str):
        pass