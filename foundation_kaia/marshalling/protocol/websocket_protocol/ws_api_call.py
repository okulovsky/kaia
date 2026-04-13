import json
from typing import Any

import websocket as ws_client

from ..model import ResultType, CallModel
from ..model.file_like import FileLikeHandler
from ...serialization import SerializationContext


_MAX_RAW_ITEMS = 5


def ws_api_call(data: CallModel) -> Any:
    """Make a WebSocket call for the given CallModel and return the result."""
    url = data.base_url.rstrip('/') + data.content.url
    ws_url = url.replace('http://', 'ws://').replace('https://', 'wss://')

    ws = ws_client.create_connection(ws_url)
    try:
        # Send JSON args
        ws.send(json.dumps({'type': 'args', 'json': data.content.json}))

        # Send files
        for name, filelike in data.content.files.items():
            ws.send(json.dumps({'type': 'file', 'name': name}))
            ws.send_binary(FileLikeHandler.to_bytes(filelike))

        # Send binary stream
        if data.content.binary_stream is not None:
            stream = data.content.binary_stream
            ws.send(json.dumps({'type': 'stream', 'name': stream.name}))
            for chunk in stream.iterable:
                ws.send_binary(chunk)
            ws.send(json.dumps({'type': 'end'}))

        # Send custom stream
        elif data.content.custom_stream is not None:
            stream = data.content.custom_stream
            ws.send(json.dumps({'type': 'stream', 'name': stream.name}))
            ctx = SerializationContext()
            for item in stream.iterable:
                json_item = stream.serializer.to_json(item, ctx)
                ws.send(json.dumps({'type': 'item', 'value': json_item}))
            ws.send(json.dumps({'type': 'end'}))

        return _receive_result(ws, data.endpoint_model)

    except Exception:
        try:
            ws.close()
        except Exception:
            pass
        raise


def _receive_result(ws: ws_client.WebSocket, model) -> tuple[Any, Any]:
    """Receive and return (result, raw_json) from the server."""
    msg = json.loads(ws.recv())

    if msg['type'] == 'error':
        ws.close()
        raise Exception(msg['message'])

    if msg['type'] == 'result':
        ws.close()
        raw = msg['value']
        ctx = SerializationContext()
        return model.result.serializer.from_json(raw, ctx), raw

    if msg['type'] == 'stream':
        if model.result.type == ResultType.BinaryFile:
            return _start_binary_stream(ws), None
        else:
            raw_items = []
            return _start_custom_stream(ws, model, raw_items), raw_items

    raise ValueError(f"Unexpected message type: {msg['type']}")


def _start_binary_stream(ws: ws_client.WebSocket):
    """Peek at the first frame to detect immediate errors before returning the generator.
    This mirrors how the HTTP server eagerly reads the first chunk before responding."""
    opcode, data = ws.recv_data()
    if opcode == ws_client.ABNF.OPCODE_TEXT:
        msg = json.loads(data.decode())
        if msg['type'] == 'end':
            ws.close()
            return iter([])
        elif msg['type'] == 'error':
            ws.close()
            raise Exception(msg['message'])
        raise ValueError(f"Unexpected text message in binary stream: {msg}")
    # First frame is a binary chunk — return a generator starting with it
    return _binary_stream_from(ws, data)


def _binary_stream_from(ws: ws_client.WebSocket, first_chunk: bytes):
    """Generator that yields the first buffered chunk then continues reading."""
    try:
        yield first_chunk
        while True:
            opcode, data = ws.recv_data()
            if opcode == ws_client.ABNF.OPCODE_BINARY:
                yield data
            elif opcode == ws_client.ABNF.OPCODE_TEXT:
                msg = json.loads(data.decode())
                if msg['type'] == 'end':
                    return
                elif msg['type'] == 'error':
                    raise Exception(msg['message'])
    finally:
        try:
            ws.close()
        except Exception:
            pass


def _start_custom_stream(ws: ws_client.WebSocket, model, raw_items: list):
    """Peek at the first message to detect immediate errors before returning the generator."""
    text = ws.recv()
    msg = json.loads(text)
    if msg['type'] == 'end':
        ws.close()
        return iter([])
    elif msg['type'] == 'error':
        ws.close()
        raise Exception(msg['message'])
    elif msg['type'] == 'item':
        ctx = SerializationContext()
        if len(raw_items) < _MAX_RAW_ITEMS:
            raw_items.append(msg['value'])
        first_item = model.result.serializer.from_json(msg['value'], ctx)
        return _custom_stream_from(ws, model, first_item, raw_items)
    raise ValueError(f"Unexpected message in custom stream: {msg}")


def _custom_stream_from(ws: ws_client.WebSocket, model, first_item, raw_items: list):
    """Generator that yields the first buffered item then continues reading."""
    try:
        yield first_item
        while True:
            text = ws.recv()
            msg = json.loads(text)
            if msg['type'] == 'end':
                return
            elif msg['type'] == 'error':
                raise Exception(msg['message'])
            elif msg['type'] == 'item':
                ctx = SerializationContext()
                if len(raw_items) < _MAX_RAW_ITEMS:
                    raw_items.append(msg['value'])
                yield model.result.serializer.from_json(msg['value'], ctx)
    finally:
        try:
            ws.close()
        except Exception:
            pass
