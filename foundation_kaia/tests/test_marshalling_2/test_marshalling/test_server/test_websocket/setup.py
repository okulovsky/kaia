from collections.abc import Iterable
from dataclasses import dataclass
from foundation_kaia.marshalling_2.marshalling.model import websocket, EndpointModel, FileLike
from foundation_kaia.marshalling_2.marshalling.server import Server, EndpointComponent, ApiCall, TestApi


@dataclass
class Data:
    value: int


class ExampleWsImpl:
    @websocket(verify_abstract=False)
    def path_query(self, id: int, flag: bool | None = None) -> str:
        return f"path_query:{id},{flag}"

    @websocket(verify_abstract=False)
    def path_query_json(self, id: int, data: Data, flag: bool | None = None) -> str:
        return f"path_query_json:{id},{flag},{data.value}"

    @websocket(verify_abstract=False)
    def path_query_json_files(self, id: int, data: Data, f1: FileLike, f2: FileLike, flag: bool | None = None) -> str:
        return f"path_query_json_files:{id},{flag},{data.value},{len(f1)},{len(f2)}"

    @websocket(verify_abstract=False)
    def path_query_file(self, id: int, f: FileLike, flag: bool | None = None) -> str:
        return f"path_query_file:{id},{flag},{len(f)}"

    @websocket(verify_abstract=False)
    def path_query_stream(self, id: int, data: Iterable[bytes], flag: bool | None = None) -> str:
        return f"path_query_stream:{id},{flag},{sum(len(chunk) for chunk in data)}"

    # WebSocket-exclusive: streaming output (CustomIterable)
    @websocket(verify_abstract=False)
    def stream_output(self, id: int) -> Iterable[str]:
        for i in range(3):
            yield f"item:{id}:{i}"

    # WebSocket-exclusive: JSON params + binary stream input (not allowed in HTTP)
    @websocket(verify_abstract=False)
    def json_and_stream(self, id: int, data: Data, stream: Iterable[bytes]) -> str:
        total = sum(len(chunk) for chunk in stream)
        return f"json_and_stream:{id},{data.value},{total}"

    # WebSocket-exclusive: FileLike + Iterable[bytes] input (not allowed in HTTP)
    @websocket(verify_abstract=False)
    def file_and_stream(self, id: int, f: FileLike, stream: Iterable[bytes]) -> str:
        total = sum(len(chunk) for chunk in stream)
        return f"file_and_stream:{id},{len(f)},{total}"

    # WebSocket-exclusive: streaming input AND streaming output simultaneously
    @websocket(verify_abstract=False)
    def roundtrip(self, data: Iterable[bytes]) -> Iterable[bytes]:
        return data


class ExampleWsServer(Server):
    def __init__(self, port: int):
        impl = ExampleWsImpl()
        super().__init__(
            port,
            EndpointComponent(impl.path_query),
            EndpointComponent(impl.path_query_json),
            EndpointComponent(impl.path_query_json_files),
            EndpointComponent(impl.path_query_file),
            EndpointComponent(impl.path_query_stream),
            EndpointComponent(impl.stream_output),
            EndpointComponent(impl.json_and_stream),
            EndpointComponent(impl.file_and_stream),
            EndpointComponent(impl.roundtrip),
        )


class ExampleWsApi:
    def __init__(self, base_url: str):
        self.path_query = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.path_query))
        self.path_query_json = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.path_query_json))
        self.path_query_json_files = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.path_query_json_files))
        self.path_query_file = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.path_query_file))
        self.path_query_stream = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.path_query_stream))
        self.stream_output = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.stream_output))
        self.json_and_stream = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.json_and_stream))
        self.file_and_stream = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.file_and_stream))
        self.roundtrip = ApiCall(base_url, EndpointModel.parse(ExampleWsImpl.roundtrip))

    @staticmethod
    def test() -> 'TestApi[ExampleWsApi]':
        return TestApi(ExampleWsApi, ExampleWsServer(8878))
