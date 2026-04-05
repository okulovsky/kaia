import asyncio
import traceback
from typing import Any, Callable
from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from ..model import EndpointRegistrationData, ResultType, FileLikeHandler, parse_url
from ...serialization import SerializationContext
from .parse_content import parse_content


def http_endpoint(data: EndpointRegistrationData) -> Callable:
    """Build and return a FastAPI request handler for the given endpoint."""
    model = data.endpoint
    service = data.service

    async def handler(request: Request):
        kwargs: dict[str, Any] = {}

        try:
            parse_url(kwargs, model, request.path_params, request.query_params)
        except ValueError as e:
            return Response(content=str(e), status_code=400)

        content_type = request.headers.get('content-type', '')

        if model.params.json_params or model.params.file_params or model.params.binary_stream_param:
            loop = asyncio.get_running_loop()
            q: asyncio.Queue = asyncio.Queue()

            async def fill_queue():
                try:
                    async for chunk in request.stream():
                        if chunk:
                            await q.put(chunk)
                finally:
                    await q.put(None)

            def sync_stream():
                while True:
                    chunk = asyncio.run_coroutine_threadsafe(q.get(), loop).result()
                    if chunk is None:
                        break
                    yield chunk

            fill_task = asyncio.create_task(fill_queue())

            def run():
                parse_content(kwargs, content_type, sync_stream(), model)
                return service(**kwargs)

            try:
                result = await loop.run_in_executor(None, run)
            except Exception:
                fill_task.cancel()
                return Response(content=traceback.format_exc(), status_code=500)
            await fill_task

        else:
            loop = asyncio.get_running_loop()
            try:
                result = await loop.run_in_executor(None, lambda: service(**kwargs))
            except Exception:
                return Response(content=traceback.format_exc(), status_code=500)

        if model.result.type == ResultType.BinaryFile:
            result_ct = model.result.content_type
            result_iter = iter(FileLikeHandler.to_bytes_iterable(result))
            try:
                first_chunk = next(result_iter)
            except StopIteration:
                return Response(b'', media_type=result_ct)
            except Exception:
                return Response(content=traceback.format_exc(), status_code=500)

            def stream():
                yield first_chunk
                yield from result_iter

            return StreamingResponse(stream(), media_type=result_ct)

        try:
            ctx = SerializationContext()
            json_value = model.result.serializer.to_json(result, ctx)
        except Exception:
            return Response(content=traceback.format_exc(), status_code=500)
        return JSONResponse(json_value)

    return handler


def build_route_path(model, address: str | None = None) -> str:
    """Build the FastAPI route string including path parameter placeholders."""
    parts = [address if address is not None else model.endpoint_address]
    for param in model.params.path_params:
        parts.append(f'{{{param.name}}}')
    if model.params.pathlike_param is not None:
        parts.append(f'{{{model.params.pathlike_param.name}:path}}')
    return '/' + '/'.join(parts)
