from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from .web_app_entry_point import WebAppEntryPoint
from .components import IComponent
from abc import ABC, abstractmethod

class IServer(ABC):
    @abstractmethod
    def get_port(self) -> int:
        pass

    @abstractmethod
    def create_web_app_entry_point(self) -> WebAppEntryPoint:
        pass

    def __call__(self):
        wp = self.create_web_app_entry_point()
        print(f"Starting server on http://127.0.0.1:{self.get_port()}")
        wp.run()



class Server(IServer):
    def __init__(self, port: int, *components: IComponent):
        self._port = port
        self.components = components

    def get_port(self) -> int:
        return self._port

    def create_web_app_entry_point(self):
        app = FastAPI()

        @app.get('/')
        def index():
            return PlainTextResponse("OK")

        @app.get('/heartbeat')
        def heartbeat():
            return PlainTextResponse("OK")

        for component in self.components:
            component.mount(app)

        return WebAppEntryPoint(app, self._port)

