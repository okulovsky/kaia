import unittest
from .setup import *

from collections.abc import Iterable
from dataclasses import dataclass
from foundation_kaia.marshalling import endpoint, EndpointModel, FileLike, service, Server, ServiceComponent, ApiCall, TestApi


@dataclass
class Data:
    value: int

@service
class ExampleImpl:
    @endpoint(verify_abstract=False)
    def path_query(self, id: int, flag: bool | None = None) -> str:
        return f"path_query:{id},{flag}"

    @endpoint(verify_abstract=False)
    def path_query_json(self, id: int, data: Data, flag: bool | None = None) -> str:
        return f"path_query_json:{id},{flag},{data.value}"

    @endpoint(verify_abstract=False)
    def path_query_json_files(self, id: int, data: Data, f1: FileLike, f2: FileLike, flag: bool | None = None) -> str:
        return f"path_query_json_files:{id},{flag},{data.value},{len(f1)},{len(f2)}"

    @endpoint(verify_abstract=False)
    def path_query_file(self, id: int, f: FileLike, flag: bool | None = None) -> str:
        return f"path_query_file:{id},{flag},{len(f)}"

    @endpoint(verify_abstract=False)
    def path_query_stream(self, id: int, data: Iterable[bytes], flag: bool | None = None) -> str:
        return f"path_query_stream:{id},{flag},{sum(len(chunk) for chunk in data)}"


class ExampleServer(Server):
    def __init__(self, port: int):
        impl = ExampleImpl()
        super().__init__(port, ServiceComponent(impl))


class ExampleApi(ExampleImpl):
    def __init__(self, base_url: str, custom_prefix: str | None = None):
        ApiCall.define_endpoints(self, base_url, ExampleImpl, custom_prefix)

    @staticmethod
    def test() -> 'TestApi[ExampleApi]':
        return TestApi(ExampleApi, ExampleServer(8888))

class TestIntegration(unittest.TestCase):
    def test_integration(self):
        with ExampleApi.test() as api:
            result = api.path_query(1, True)
            self.assertEqual("path_query:1,True", result)

            result = api.path_query_json(2, Data(5), False)
            self.assertEqual("path_query_json:2,False,5", result)

            result = api.path_query_json_files(3, Data(7), b'hello', b'world', True)
            self.assertEqual("path_query_json_files:3,True,7,5,5", result)

            result = api.path_query_file(4, b'test', True)
            self.assertEqual("path_query_file:4,True,4", result)

            result = api.path_query_stream(5, iter([b'abc', b'def']), False)
            self.assertEqual("path_query_stream:5,False,6", result)


class PrefixServer(Server):
    def __init__(self, port: int):
        impl = ExampleImpl()
        super().__init__(port, ServiceComponent(impl, prefix='test'))


class TestPrefix(unittest.TestCase):
    def test_prefix(self):
        with TestApi(ExampleApi, PrefixServer(8889)) as _:
            import requests
            response = requests.post('http://127.0.0.1:8889/test/path-query/1')
            self.assertEqual(200, response.status_code)
            self.assertEqual("path_query:1,None", response.json())

            api = ExampleApi(base_url='http://127.0.0.1:8889', custom_prefix='test')
            result = api.path_query(1)
            self.assertEqual("path_query:1,None", result)



if __name__ == '__main__':
    unittest.main()
