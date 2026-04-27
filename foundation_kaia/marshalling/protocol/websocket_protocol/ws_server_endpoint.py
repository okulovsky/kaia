import asyncio
import json
import threading
from typing import Any, Callable

from fastapi import WebSocket

from ..model import EndpointRegistrationData, ResultType, FileLikeHandler, parse_url, parse_json
from ...serialization import SerializationContext
from .queue_iterable import QueueIterable


def ws_endpoint(data: EndpointRegistrationData) -> Callable:
    """Build and return a FastAPI WebSocket handler for the given endpoint."""
    model = data.endpoint
    service = data.service

    async def handler(websocket: WebSocket):
        await websocket.accept()
        kwargs: dict[str, Any] = {}

        # Parse URL path/query params
        try:
            parse_url(kwargs, model, websocket.path_params, websocket.query_params)
        except ValueError as e:
            await websocket.send_text(json.dumps({'type': 'error', 'message': str(e)}))
            await websocket.close()
            return

        # Receive args message
        try:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            parse_json(kwargs, msg.get('json', {}), model.params.json_params)
        except Exception as e:
            await websocket.send_text(json.dumps({'type': 'error', 'message': str(e)}))
            await websocket.close()
            return

        # Receive files (in declaration order)
        for file_arg in model.params.file_params:
            meta = json.loads(await websocket.receive_text())
            name = meta['name']
            kwargs[name] = await websocket.receive_bytes()

        # Set up input stream queue if an input stream is expected
        input_queue: QueueIterable | None = None
        is_binary_stream = model.params.binary_stream_param is not None
        is_custom_stream = model.params.custom_stream_param is not None

        if is_binary_stream or is_custom_stream:
            stream_msg = json.loads(await websocket.receive_text())
            stream_name = stream_msg['name']
            input_queue = QueueIterable()
            kwargs[stream_name] = input_queue

        loop = asyncio.get_running_loop()

        if input_queue is not None:
            item_serializer = (
                model.params.custom_stream_param.serializer if is_custom_stream else None
            )

            async def fill_stream():
                try:
                    while True:
                        raw_msg = await websocket.receive()
                        if 'bytes' in raw_msg and raw_msg['bytes']:
                            input_queue.put(raw_msg['bytes'])
                        elif 'text' in raw_msg and raw_msg['text']:
                            parsed = json.loads(raw_msg['text'])
                            if parsed['type'] == 'end':
                                input_queue.end()
                                return
                            elif parsed['type'] == 'item' and item_serializer is not None:
                                ctx = SerializationContext()
                                item = item_serializer.from_json(parsed['value'], ctx)
                                input_queue.put(item)
                except Exception:
                    input_queue.end()

            fill_task = asyncio.create_task(fill_stream())
            try:
                result = await loop.run_in_executor(None, lambda: service(**kwargs))
            except Exception as e:
                fill_task.cancel()
                await websocket.send_text(json.dumps({'type': 'error', 'message': str(e)}))
                await websocket.close()
                return
            await fill_task
        else:
            try:
                result = await loop.run_in_executor(None, lambda: service(**kwargs))
            except Exception as e:
                await websocket.send_text(json.dumps({'type': 'error', 'message': str(e)}))
                await websocket.close()
                return

        await _send_result(websocket, result, model)
        await websocket.close()

    return handler


async def _send_result(ws: WebSocket, result, model):
    """Send the service result back to the client over the WebSocket."""
    if model.result.type == ResultType.Json:
        ctx = SerializationContext()
        json_value = model.result.serializer.to_json(result, ctx)
        await ws.send_text(json.dumps({'type': 'result', 'value': json_value}))
        return

    # Streaming result (BinaryFile or CustomIterable) — run iteration in a thread,
    # fan results through an asyncio queue so we can await each send.
    loop = asyncio.get_event_loop()
    q: asyncio.Queue = asyncio.Queue()

    def iterate():
        try:
            if model.result.type == ResultType.BinaryFile:
                for chunk in FileLikeHandler.to_bytes_iterable(result):
                    asyncio.run_coroutine_threadsafe(q.put(('bytes', chunk)), loop)
            else:  # CustomIterable
                ctx = SerializationContext()
                for item in result:
                    json_item = model.result.serializer.to_json(item, ctx)
                    asyncio.run_coroutine_threadsafe(q.put(('json', json_item)), loop)
            asyncio.run_coroutine_threadsafe(q.put(('done', None)), loop)
        except Exception as e:
            asyncio.run_coroutine_threadsafe(q.put(('error', str(e))), loop)

    await ws.send_text(json.dumps({'type': 'stream'}))
    thread = threading.Thread(target=iterate)
    thread.start()

    while True:
        tag, val = await q.get()
        if tag == 'done':
            await ws.send_text(json.dumps({'type': 'end'}))
            break
        elif tag == 'error':
            await ws.send_text(json.dumps({'type': 'error', 'message': val}))
            break
        elif tag == 'bytes':
            await ws.send_bytes(val)
        elif tag == 'json':
            await ws.send_text(json.dumps({'type': 'item', 'value': val}))

    thread.join()
