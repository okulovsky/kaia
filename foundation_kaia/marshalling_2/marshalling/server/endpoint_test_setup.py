from threading import Thread
from typing import Callable, TypeVar, Generic, Type
import uvicorn
from .components import EndpointComponent
from .server import IServer, Server
from .utils import ApiUtils
from .api_call import ApiCall
from foundation_kaia.fork import Fork

T = TypeVar('T')


class TestApi(Generic[T]):
    def __init__(self, api_class: Type[T], server: IServer, on_exit: Callable | None = None):
        self.api_class = api_class
        self.server = server
        self.on_exit = on_exit
        self._fork: Fork | None = None

    def __enter__(self) -> T:
        self._fork = Fork(self.server, raise_if_exited=False).start()
        base_url = f'http://127.0.0.1:{self.server.get_port()}'
        ApiUtils.wait_for_reply(base_url, 10)
        return self.api_class(base_url)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fork is not None:
            self._fork.terminate()
        if self.on_exit is not None:
            self.on_exit()


class ThreadTestApi(Generic[T]):
    def __init__(self, api_class: Type[T], server: IServer, on_exit: Callable | None = None):
        self.api_class = api_class
        self.server = server
        self.on_exit = on_exit
        self._uvicorn_server: uvicorn.Server | None = None
        self._thread: Thread | None = None

    def __enter__(self) -> T:
        entry_point = self.server.create_web_app_entry_point()
        for callable in entry_point.daemon_threads:
            Thread(target=callable, daemon=True).start()
        config = uvicorn.Config(entry_point.app, host=entry_point.host, port=entry_point.port, log_level='warning')
        self._uvicorn_server = uvicorn.Server(config)
        self._thread = Thread(target=self._uvicorn_server.run, daemon=True)
        self._thread.start()
        base_url = f'http://127.0.0.1:{self.server.get_port()}'
        ApiUtils.wait_for_reply(base_url, 10)
        return self.api_class(base_url)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._uvicorn_server is not None:
            self._uvicorn_server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)
        if self.on_exit is not None:
            self.on_exit()


class TestEndpointApi:
    def __init__(self, method: Callable, port: int = 11512):
        self.method = method
        self.port = port
        self._fork: Fork | None = None

    def __enter__(self) -> ApiCall:
        component = EndpointComponent(self.method)
        server = Server(self.port, component)
        self._fork = Fork(server, raise_if_exited=False).start()
        base_url = f'http://127.0.0.1:{self.port}'
        ApiUtils.wait_for_reply(base_url, 10)
        return ApiCall(base_url, component.model)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fork is not None:
            self._fork.terminate()
