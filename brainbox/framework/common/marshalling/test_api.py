from typing import TypeVar, Generic, Callable
from .server import Server
from .api import Api
from ..fork import Fork

TApi = TypeVar('TApi')

class TestApi(Generic[TApi]):
    def __init__(self,
                 api_factory: Callable[[str], Api],
                 server: Server
                 ):
        self.api_factory = api_factory
        self.server = server
        self.fork = None

    def __enter__(self) -> TApi:
        self.fork = Fork(self.server).start()
        api = self.api_factory(f'127.0.0.1:{self.server.port}')
        api.wait()
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fork is not None:
            self.fork.terminate()


