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
        params = data.endpoint_model.params

        # Send JSON args
        ws.send(json.dumps({'type': 'args', 'json': data.content.json_values}))

        # Send files
        for param in params.file_params:
            ws.send(json.dumps({'type': 'file', 'name': param.name}))
            ws.send_binary(FileLikeHandler.to_bytes(data.content.raw_values[param.name]))

        # Send binary stream
        if params.binary_stream_param is not None:
            name = params.binary_stream_param.name
            ws.send(json.dumps({'type': 'stream', 'name': name}))
            for chunk in data.content.raw_values[name]:
                ws.send_binary(chunk)
            ws.send(json.dumps({'type': 'end'}))

        # Send custom stream
        elif params.custom_stream_param is not None:
            name = params.custom_stream_param.name
            ws.send(json.dumps({'type': 'stream', 'name': name}))
            ctx = SerializationContext()
            for item in data.content.raw_values[name]:
                json_item = params.custom_stream_param.serializer.to_json(item, ctx)
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
