import requests
from abc import ABC, abstractmethod
from flask import Flask

class Component(ABC):
    @abstractmethod
    def register(self, app: Flask):
        pass

class BlueprintComponent(Component):
    def register(self, app: Flask):
        app.register_blueprint(self.create_blueprint())

    @abstractmethod
    def create_blueprint(self):
        pass

class ApiError(requests.HTTPError):
    def __init__(self, resp: requests.Response):
        self.response = resp
        body = resp.text if resp.text else resp.content
        super().__init__(f"{resp.status_code} {resp.reason} {resp.request.method} {resp.url}\n\n{body!r}")

    @staticmethod
    def check(resp: requests.Response):
        if not resp.ok:
            _ = resp.text
            raise ApiError(resp)
        return resp
