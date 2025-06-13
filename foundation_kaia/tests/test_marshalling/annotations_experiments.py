from foundation_kaia.marshalling import Api, bind_to_api, endpoint, TestApi, Server
from abc import abstractmethod, ABC

class IMy(ABC):
    @abstractmethod
    def test(self, a: int, b: str = ''):
        pass

class My(IMy):
    @endpoint()
    def test(self, a: int, b: str = ''):
        return f'{a},{b}'

@bind_to_api(My)
class MyApi(Api, IMy):
    pass

    class Test(TestApi['MyApi']):
        def __init__(self):
            super().__init__(MyApi, Server(My(), 8092))


if __name__ == '__main__':
    with MyApi.Test() as api:
        pass
