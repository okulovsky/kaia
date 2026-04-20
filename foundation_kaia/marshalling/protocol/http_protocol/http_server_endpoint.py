import asyncio
import traceback
from typing import Any, Callable
from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from ..model import EndpointRegistrationData, ResultType, FileLikeHandler, parse_url
from ...serialization import SerializationContext
from .parse_content import parse_content


class HttpEndpointHandler:
    def __init__(self, data: EndpointRegistrationData):
        self.model = data.endpoint
        self.service = data.service

    async def _fill_queue(self, request: Request, q: asyncio.Queue) -> None:
        """Stream request body chunks into an async queue, then signal completion with None."""
        try:
            async for chunk in request.stream():
                if chunk:
                    await q.put(chunk)
        finally:
            await q.put(None)

    def _sync_stream(self, q: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        """Yield body chunks from the async queue in a synchronous context."""
        while True:
            chunk = asyncio.run_coroutine_threadsafe(q.get(), loop).result()
            if chunk is None:
                break
            yield chunk

    def _parse_and_call(self, kwargs: dict, content_type: str, q: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> Any:
        """Parse the request body into kwargs, then call the service method."""
        parse_content(kwargs, self._sync_stream(q, loop), self.model, content_type)
        return self.service(**kwargs)

    def _build_binary_response(self, result) -> Response:
        """Wrap a binary file result as a StreamingResponse."""
        result_ct = self.model.result.content_type
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

    def _build_json_response(self, result) -> Response:
        """Serialize the result to JSON and return a JSONResponse."""
        try:
            ctx = SerializationContext()
            json_value = self.model.result.serializer.to_json(result, ctx)
        except Exception:
            return Response(content=traceback.format_exc(), status_code=500)
        return JSONResponse(json_value)

    async def handle(self, request: Request) -> Response:
        """Parse URL params, stream and parse the body, call the service, and return the response."""
        kwargs: dict[str, Any] = {}

        try:
            parse_url(kwargs, self.model, request.path_params, request.query_params)
        except ValueError as e:
            return Response(content=str(e), status_code=400)

        content_type = request.headers.get('content-type', '')
        loop = asyncio.get_running_loop()

        if self.model.params.json_params or self.model.params.file_params or self.model.params.binary_stream_param:
            q: asyncio.Queue = asyncio.Queue()
            fill_task = asyncio.create_task(self._fill_queue(request, q))
            try:
                result = await loop.run_in_executor(None, lambda: self._parse_and_call(kwargs, content_type, q, loop))
            except Exception:
                fill_task.cancel()
                return Response(content=traceback.format_exc(), status_code=500)
            await fill_task
        else:
            try:
                result = await loop.run_in_executor(None, lambda: self.service(**kwargs))
            except Exception:
                return Response(content=traceback.format_exc(), status_code=500)

        if self.model.result.type == ResultType.BinaryFile:
            return self._build_binary_response(result)
        return self._build_json_response(result)


def http_endpoint(data: EndpointRegistrationData) -> Callable:
    """Create a FastAPI request handler for the given endpoint."""
    return HttpEndpointHandler(data).handle


def build_route_path(model, address: str | None = None) -> str:
    """Build the FastAPI route string including path parameter placeholders."""
    parts = [address if address is not None else model.endpoint_address]
    for param in model.params.path_params:
        parts.append(f'{{{param.name}}}')
    if model.params.pathlike_param is not None:
        parts.append(f'{{{model.params.pathlike_param.name}:path}}')
    return '/' + '/'.join(parts)
