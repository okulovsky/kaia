# Table of contents

* [foundation_kaia](#foundation_kaia)
  * [Fork](#fork)
  * [Marshalling](#marshalling)
    * [Essentials](#essentials)
    * [Calling server outside of Python](#calling-server-outside-of-python)
    * [Files](#files)
    * [WebSockets and Streaming](#websockets-and-streaming)
    * [Serialization](#serialization)
      * [Dataclasses](#dataclasses)
      * [Additional primitives](#additional-primitives)
      * [Bytes](#bytes)
      * [SQLAlchemy entities](#sqlalchemy-entities)
      * [Polymorphism](#polymorphism)
      * [Unsupported data](#unsupported-data)

# foundation_kaia

`foundation_kaia` is a utility library that provides the core building blocks used across the kaia ecosystem:
networking/RPC via `marshalling`, subprocess isolation via `fork`, template rendering via `prompters`,
and various shared utilities.

## Fork

Fork is a small utility to run the functions in a different subprocess: particularly the web-servers to ensure full isolation.

You can define the callable, and then use Fork like this:

```python
from foundation_kaia import Fork

with Fork(callable):
    # Do useful work
    pass
```

There are also `.start()` and `.terminate()` methods if you do not want to use the context manager.
Mostly, `Fork` is used for unit testing and the documentation purposes, so, with the context manager.

## Marshalling

Submodule `marshalling` organizes remote procedure call for python code via HTTP/websockets protocol and simple
comminucation format that is easy to reproduce outside of python.

### Essentials

`marshalling` starts with defining the interface with the desired functionality:

```python
from foundation_kaia.marshalling import service, endpoint
from typing import Any

@service
class IMyService:
    @endpoint
    def select(self, id: str, data: list[dict[str, Any]], drop_duplicates: bool|None = None) -> list[str]:
        ...
```

This interface needs to be implemented in the service:

```python
class MyService(IMyService):
    def select(self, id: str, data: list[dict[str, Any]], drop_duplicates: bool|None = None) -> list[str]:
        result = []
        for element in data:
            if element['id'] == id:
                if drop_duplicates and element['text'] in result:
                    continue
                result.append(element['text'])
        return result
```

This is enough to create a web-server that will serve `MyService`, exposing it's methods (marked with `@endpoint`)
as the server's endpoints. Also, you can create an API that will implement `IMyService`, therefore providing a direct
replacement for the direct call of `IMyService` methods:  

```python
from foundation_kaia.marshalling import ApiCall, Server, ServiceComponent, ApiUtils
from foundation_kaia.fork import Fork

PORT = 14000

class MyApi(IMyService):
    def __init__(self, base_url: str):
        ApiCall.define_endpoints(self, base_url, IMyService)


if __name__ == '__main__':
    server = Server(PORT, ServiceComponent(MyService()))

    with Fork(server):
        base_url = f"http://localhost:{PORT}"
        ApiUtils.wait_for_reply(base_url, 10)
        api = MyApi(base_url)
        result = api.select(
            'test',
            [
                {'id': 'test', 'text': 'example 1'},
                {'id': 'test', 'text': 'example 2'},
                {'id': 'test', 'text': 'example 1'},
                {'id': 'test_1', 'text': 'example 3'},
            ],
            True
        )
```

After this, `result` will be:

```
['example 1', 'example 2']
```

### Calling server outside of Python

The server can be called without API and python, as a plain HTTP server. The parameters should be passed as:

* primitives, non-nullable: as a part of the url path in the order of appearence in the method
* primitives, nullable: as a part of the query string
* others: in JSON body. 

If you do not wish these complications, you may use `force_json_params` parameter of `@endpoint` decorator.

Now, let's call out server:

```python
import requests


if __name__ == '__main__':
    server = Server(PORT, ServiceComponent(MyService()))

    with Fork(server):
        ApiUtils.wait_for_reply(f"http://localhost:{PORT}", 10)
        response = requests.post(
            f"http://localhost:{PORT}/my-service/select/test/?drop_duplicates=True",
            json=dict(data=[
                {'id': 'test', 'text': 'example 1'},
                {'id': 'test', 'text': 'example 2'},
                {'id': 'test', 'text': 'example 1'},
                {'id': 'test_1', 'text': 'example 3'},
            ]))
        response.raise_for_status()
```

`response.json()` will be:

```
['example 1', 'example 2']
```

To get a reference of the services, endpoints, as well as JsonSchema for the passing jsons, please use this: 

```python
from foundation_kaia.marshalling.documenter import ApiDocumentation


documentation = ApiDocumentation.parse(MyApi)
```

For instance, `documentation.services['my-service'].endpoints['select']` is:

```
EndpointDocumentation(name='select',
                      docstring=None,
                      url_template='/my-service/select/<id>?drop_duplicates=<drop_duplicates>',
                      json_schema=JsonSchema(schema={'properties': {'data': {'items': {'additionalProperties': {},
                                                                                       'type': 'object'},
                                                                             'type': 'array'}},
                                                     'type': 'object'},
                                             defs={}),
                      file_params=[],
                      return_type='list',
                      return_is_file=False)
```

### Files

Marshalling can handle incoming files in two different ways:

* Normal files: collected in the buffer at the server's side, and then delivered to the method as blob of bytes. The arguments that have `bytes` in their type annotation will be such normal files. The more practical way is to use `FileLike` annotation, that allows you to send Path, str, bytes and `File` objects.
* Streams: transfered bit-by-bit and delivered to the method as `Iterable[bytes]`, so they can be processed bit by bit. The arguments with Iterable[bytes] in their annotation will be streaming files. Iterable[bytes]|FileLike is also a streaming file.

Depending on the combination of the arguments, following structures in the requests' body are possible:

* Only json-parameters, no file: the body will be JSON (Content-Type will be set application/json)
* A single file, normal or stream: the body will be this file (Content-Type will be set to application/octet-stream)
* A mix of normal files and json-parameters: multipart-form containing `json_arguments` part with json and the files
* Other combinations are not possible in HTTP protocol, but can be used in WebSockets. Also, the structure when the endpoint consumes a file bit-by-bit and produces the output file bit-by-bit, is not possible in HTTP protocol.

If the output of the endpoint is file, it is always streamed.

Let's define a service that demonstrates all the HTTP-compatible combinations, using them with `requests` library. API doesn't really need an additional demonstration as all of these cases are processed under the hood with API remaning the drop-in replacement for the service in the codebase.

We will use `force_json_params=True` to ensure the arguments end up in the JSON, not in the query params or url.

We will also use `verify_abstract=False` argument to merge interface with the service. It's not normally needed as the clear separation between the interface and the service is important, but in the testing environment, it's handy to unite them in one class.

`FileLikeHandler` is a type-hint-friendly and convenient class that will transform all the files to the bytes at the server's side.   

```python
from foundation_kaia.marshalling import service, endpoint, FileLike, FileLikeHandler
from collections.abc import Iterable

@service
class IFileService:
    @endpoint(force_json_params=True, verify_abstract=False)
    def json_only(self, name: str) -> str:
        return name

    @endpoint(verify_abstract=False)
    def single_file(self, file: FileLike|Iterable[bytes]) -> int:
        return len(FileLikeHandler.to_bytes(file))

    @endpoint(force_json_params=True, verify_abstract=False)
    def json_and_file(self, name: str, file: FileLike) -> int:
        return len(FileLikeHandler.to_bytes(file))

    @endpoint(force_json_params=True, verify_abstract=False)
    def download_file(self, content: str) -> Iterable[bytes]:
        encoded = content.encode('utf-8')
        chunk_size = 4
        for i in range(0, len(encoded), chunk_size):
            yield encoded[i:i + chunk_size]
```

Now let's run the server and call each endpoint with `requests` to see the body structures.

```python
import json
import requests
from foundation_kaia.marshalling import Server, ServiceComponent, ApiUtils
from foundation_kaia.fork import Fork

PORT = 14010


if __name__ == '__main__':
    server = Server(PORT, ServiceComponent(IFileService()))

    with Fork(server):
        ApiUtils.wait_for_reply(f"http://localhost:{PORT}", 10)
```

JSON-only: the data sent is a JSON with the required arguments.

```python
response = requests.post(
    f"http://localhost:{PORT}/file-service/json-only",
    json={"name": "hello"},
)
response.raise_for_status()
```

`response.json()` is:

```
'hello'
```

Single file / stream:

```python
response = requests.post(
    f"http://localhost:{PORT}/file-service/single-file",
    data=b"hello",
)
response.raise_for_status()
```

`response.json()` is the total byte count:

```
5
```

JSON and file

```python
response = requests.post(
    f"http://localhost:{PORT}/file-service/json-and-file",
    files=[
        ('json_arguments', json.dumps({"name": "report"})),
        ('file', b'hello'),
    ],
)
response.raise_for_status()
```

`response.json()` is:

```
5
```

Downloading a file: the response body is a stream of bytes regardless of how many chunks
the server yields. Use `stream=True` and `iter_content` to consume it, or simply read
`response.content` to collect everything at once.

```python
response = requests.post(
    f"http://localhost:{PORT}/file-service/download-file",
    json={"content": "hello"},
    stream=True,
)
response.raise_for_status()
```

`response.content` reassembles all chunks into the original bytes:

```
b'hello'
```

### WebSockets and Streaming

For endpoints that produce output incrementally — audio synthesis, token-by-token LLM responses,
or any long-running computation — use the `@websocket` decorator instead of `@endpoint`.
WebSocket endpoints share the same parameter conventions as HTTP endpoints (primitives in the URL
path, nullable primitives in the query string, JSON/file body), but they additionally support:

* Streaming output: the return type is `Iterable[bytes]`, `Iterable[str]`, or `Iterable[T]` for any serialisable `T`.
* Streaming input combined with other parameters: `Iterable[bytes]` next to JSON or `FileLike` arguments. Still, there can be only one incoming stream.
* Simultaneous streaming input and streaming output: a full-duplex round-trip over a single WebSocket connection.

Let's define a service that exercises all three variants of the streaming output:

```python
from collections.abc import Iterable
from dataclasses import dataclass

from foundation_kaia.marshalling import service, websocket, Server, ServiceComponent, ApiUtils, Serializer, SerializationContext
from foundation_kaia.fork import Fork


@dataclass
class Token:
    text: str
    index: int


@service
class IStreamingService:

    @websocket(force_json_params=True, verify_abstract=False)
    def binary_chunks(self, payload: str) -> Iterable[bytes]:
        data = payload.encode('utf-8')
        for i in range(0, len(data), 3):
            yield data[i:i + 3]

    @websocket(force_json_params=True, verify_abstract=False)
    def text_lines(self, count: int) -> Iterable[str]:
        for i in range(count):
            yield f"line:{i}"

    @websocket(force_json_params=True, verify_abstract=False)
    def token_stream(self, prompt: str) -> Iterable[Token]:
        for idx, word in enumerate(prompt.split()):
            yield Token(text=word, index=idx)
```

The wire protocol over WebSocket is straightforward:

* The client sends `{"type": "args", "json": {...}}` with the JSON-serialized parameters.
* The server replies with `{"type": "stream"}` to signal that a stream follows.
* For `Iterable[bytes]`: the server sends raw binary frames, then `{"type": "end"}`.
* For `Iterable[str]` and `Iterable[T]`: the server sends `{"type": "item", "value": ...}` text frames, then `{"type": "end"}`.

Let's demonstrate each variant using the `websocket-client` library directly:

```python
import json
import websocket as ws_client

PORT = 14020


if __name__ == '__main__':
    server = Server(PORT, ServiceComponent(IStreamingService()))

    with Fork(server):
        ApiUtils.wait_for_reply(f"http://localhost:{PORT}", 10)
```

`Iterable[bytes]` — binary frames, then `{"type": "end"}`:

```python
ws = ws_client.create_connection(f"ws://localhost:{PORT}/streaming-service/binary-chunks")
ws.send(json.dumps({"type": "args", "json": {"payload": "hello world"}}))
assert json.loads(ws.recv())["type"] == "stream"
chunks = []
while True:
    opcode, data = ws.recv_data()
    if opcode == ws_client.ABNF.OPCODE_BINARY:
        chunks.append(data)
    else:
        if json.loads(data.decode())["type"] == "end":
            break
ws.close()
```

Reassembled bytes:

```
b'hello world'
```

`Iterable[str]` — `{"type": "item", "value": "..."}` text frames:

```python
ws = ws_client.create_connection(f"ws://localhost:{PORT}/streaming-service/text-lines")
ws.send(json.dumps({"type": "args", "json": {"count": 3}}))
assert json.loads(ws.recv())["type"] == "stream"
lines = []
while True:
    msg = json.loads(ws.recv())
    if msg["type"] == "end":
        break
    lines.append(msg["value"])
ws.close()
```

Collected lines:

```
['line:0', 'line:1', 'line:2']
```

`Iterable[T]` — same text frames but `value` is the JSON-serialised dataclass.
Use `Serializer` to deserialise each item back to the original type:

```python
token_serializer = Serializer.parse(Token)
ctx = SerializationContext()

ws = ws_client.create_connection(f"ws://localhost:{PORT}/streaming-service/token-stream")
ws.send(json.dumps({"type": "args", "json": {"prompt": "hello world"}}))
assert json.loads(ws.recv())["type"] == "stream"
tokens = []
while True:
    msg = json.loads(ws.recv())
    if msg["type"] == "end":
        break
    tokens.append(token_serializer.from_json(msg["value"], ctx))
ws.close()
```

Collected tokens:

```
[Token(text='hello', index=0), Token(text='world', index=1)]
```

### Serialization

`foundation_kaia` uses its own serialization, that allows you to convert to and from JSON complex data structures.
Depending on the type annotations, `str` can be deserialized to a string, a timestamp, an Enum and so on.
`dict` can be deserialized to a dictionary, a dataclass or a sqlalchemy record.

The entry point is `Serializer.parse(type)`, which builds a serializer for any supported type.
Call `.to_json(value)` to produce a JSON-compatible value and `.from_json(json_value)` to restore the
original Python object.

There are several extensions for the plain JSON objects that are supported in this module.

#### Dataclasses

```python
from dataclasses import dataclass
from foundation_kaia.marshalling import Serializer

@dataclass
class Point:
    x: int
    y: int


if __name__ == '__main__':
    point = Serializer.parse(Point).from_json({'x': 1, 'y': 2})
```

The parsed value is:

```
Point(x=1, y=2)
```

```python
point_list = Serializer.parse(list[Point]).from_json([{'x': 1, 'y': 2}, {'x': 3, 'y': 4}])
```

The parsed list is:

```
[Point(x=1, y=2), Point(x=3, y=4)]
```

#### Additional primitives

Enums, datetime and Path are serialized as strings and deserialized as the objects of the corresponding type.
Enums are serialized and deserialized by their **name**, not their value.

```python
from enum import Enum
from datetime import datetime
from pathlib import Path

class Color(Enum):
    RED = 'red'
    GREEN = 'green'

@dataclass
class Event:
    color: Color
    when: datetime
    log_path: Path


if __name__ == '__main__':
    event = Serializer.parse(Event).from_json({
        "color": "GREEN",
        "when": "2025-01-15T12:00:00",
        "log_path": "/var/log/app.log",
    })
```

The deserialized value is:

```
Event(color=<Color.GREEN: 'green'>,
      when=datetime.datetime(2025, 1, 15, 12, 0),
      log_path=PosixPath('/var/log/app.log'))
```

#### Bytes

Bytes fields are serialized as a tagged object with a base-64 encoded value.

```python
@dataclass
class Blob:
    name: str
    content: bytes


if __name__ == '__main__':
    blob = Serializer.parse(Blob).from_json({'name': 'file.bin', 'content': {'@type': 'bytes', 'value': 'AAECAw=='}})
```

The parsed value is:

```
Blob(name='file.bin', content=b'\x00\x01\x02\x03')
```

#### SQLAlchemy entities

SQLAlchemy mapped classes are serialized and deserialized using their column attributes.

```python
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()

class UserRecord(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    score: Mapped[float | None] = mapped_column(nullable=True)


if __name__ == '__main__':
    user = Serializer.parse(UserRecord).from_json({'id': 1, 'name': 'alice', 'score': 9.5})
```

The parsed fields are:

```
{'id': 1, 'name': 'alice', 'score': 9.5}
```

#### Polymorphism

When a dataclass field is typed as a base class but holds a subclass at runtime, the serializer
adds `@type` and `@subtype` tags so the exact subclass can be reconstructed on deserialization.
When the field holds an exact instance of the declared type, no extra tags are added.

```python
@dataclass
class Shape:
    color: str

@dataclass
class Circle(Shape):
    radius: float

@dataclass
class Canvas:
    title: str
    background: Shape

from foundation_kaia.marshalling.serialization.tools import TypeTools


if __name__ == '__main__':
    canvas = Serializer.parse(Canvas).from_json({
        'title': 'art',
        'background': {
            '@type': 'dataclass',
            '@subtype': TypeTools.type_to_full_name(Circle),
            'color': 'red',
            'radius': 5.0,
        },
    })
```

The background field is reconstructed as the exact subclass; its type name is:

```
'Circle'
```

#### Unsupported data

In case the type is not supported, it will be serialized with pickle and passed as base-64 encoded bytes.
This allows the serialization/deserialization in itself to be complete and handle the cases that are not covered by supported types.
So, if you want to keep your endpoints compatible with non-python APIs, you need to use only the supported types in them.