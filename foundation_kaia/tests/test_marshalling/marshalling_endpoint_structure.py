from foundation_kaia.marshalling import endpoint, Api, TestApi, bind_to_api, Server
from abc import ABC, abstractmethod

class Buffer:
    def __init__(self, data):
        self.data = data


class IMy(ABC):
    @abstractmethod
    def hello(self, s: str) -> str:
        pass

    @abstractmethod
    def sum(self, x: int, y: int=1) -> int:
        pass

    @abstractmethod
    def custom_type(self, data) -> Buffer:
        pass

    @abstractmethod
    def custom_type_jsonpickle(self, data) -> Buffer:
        pass

    @abstractmethod
    def throwing(self):
        pass

    @abstractmethod
    def custom_url(self, s: str) -> str:
        pass

class MyImplementation(IMy):
    @endpoint(method='GET')
    def hello(self, s: str) -> str:
        return 'Hello, '+s

    @endpoint(method='POST')
    def sum(self, x: int, y: int=1) -> int:
        return x+y

    @endpoint(method='POST')
    def custom_type(self, data) -> Buffer:
        return Buffer(data)

    @endpoint(method='POST', json_pickle_result=True)
    def custom_type_jsonpickle(self, data) -> Buffer:
        return Buffer(data)

    @endpoint()
    def throwing(self):
        raise ValueError("Exception")

    @endpoint(url='/my/custom/url')
    def custom_url(self, s: str) -> str:
        return 'custom_url '+s


class MyServer(Server):
    def __init__(self):
        super().__init__(8080, MyImplementation())


class MyTestApi:
    def __init__(self,
                 api_factory,
                 server: Server
                 ):
        self.api_factory = api_factory
        self.server = server
        self.fork = None

    def __enter__(self) -> 'MyApi':
        api = self.api_factory(f'127.0.0.1:{self.server.port}')
        api.wait()
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fork is not None:
            self.fork.terminate()


@bind_to_api(MyImplementation)
class MyApi(Api, IMy):
    def __init__(self, address):
        super().__init__(address)


    class Test(TestApi['MyApi']):
        def __init__(self):
            super().__init__(MyApi, MyServer())
