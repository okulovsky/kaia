from foundation_kaia.releasing.mddoc import *

"""
### WebSockets and Streaming

For endpoints that produce output incrementally — audio synthesis, token-by-token LLM responses,
or any long-running computation — use the `@websocket` decorator instead of `@endpoint`.
WebSocket endpoints share the same parameter conventions as HTTP endpoints (primitives in the URL
path, nullable primitives in the query string, JSON/file body), but they additionally support:

* Streaming output: the return type is `Iterable[bytes]`, `Iterable[str]`, or `Iterable[T]` for any serialisable `T`.
* Streaming input combined with other parameters: `Iterable[bytes]` next to JSON or `FileLike` arguments. Still, there can be only one incoming stream.
* Simultaneous streaming input and streaming output: a full-duplex round-trip over a single WebSocket connection.

Let's define a service that exercises all three variants of the streaming output:
"""

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


"""
The wire protocol over WebSocket is straightforward:

* The client sends `{"type": "args", "json": {...}}` with the JSON-serialized parameters.
* The server replies with `{"type": "stream"}` to signal that a stream follows.
* For `Iterable[bytes]`: the server sends raw binary frames, then `{"type": "end"}`.
* For `Iterable[str]` and `Iterable[T]`: the server sends `{"type": "item", "value": ...}` text frames, then `{"type": "end"}`.

Let's demonstrate each variant using the `websocket-client` library directly:
"""

import json
import websocket as ws_client

PORT = 14020

binary_result = ControlValue.mddoc_define_control_value(b"hello world")
text_result = ControlValue.mddoc_define_control_value(["line:0", "line:1", "line:2"])
token_result = ControlValue.mddoc_define_control_value([Token("hello", 0), Token("world", 1)])

if __name__ == '__main__':
    server = Server(PORT, ServiceComponent(IStreamingService()))

    with Fork(server):
        ApiUtils.wait_for_reply(f"http://localhost:{PORT}", 10)

        """
        `Iterable[bytes]` — binary frames, then `{"type": "end"}`:
        """

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

        """
        Reassembled bytes:
        """

        binary_result.mddoc_validate_control_value(b"".join(chunks))

        """
        `Iterable[str]` — `{"type": "item", "value": "..."}` text frames:
        """

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

        """
        Collected lines:
        """

        text_result.mddoc_validate_control_value(lines)

        """
        `Iterable[T]` — same text frames but `value` is the JSON-serialised dataclass.
        Use `Serializer` to deserialise each item back to the original type:
        """

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

        """
        Collected tokens:
        """

        token_result.mddoc_validate_control_value(tokens)
