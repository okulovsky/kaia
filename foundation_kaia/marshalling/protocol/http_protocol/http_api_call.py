from typing import Any
import requests
from ..model import ResultType, CallModel
from .content_producer import ContentProducer
from ...serialization import SerializationContext


class ApiError(requests.HTTPError):
    def __init__(self, resp: requests.Response):
        body = resp.text if resp.text else resp.content
        super().__init__(
            f"{resp.status_code} {resp.reason} {resp.request.method} {resp.url}\n\n{body}",
            response=resp,
        )

    @staticmethod
    def check(resp: requests.Response):
        if not resp.ok:
            _ = resp.text
            raise ApiError(resp)
        return resp


def http_api_call(data: CallModel) -> Any:
    if data.endpoint_model.result.type == ResultType.CustomIterable:
        raise ValueError(
            f"Endpoint '{data.endpoint_model.name}' returns a CustomIterable which is not supported over HTTP. "
            f"Use WebSockets instead."
        )

    url = data.base_url.rstrip('/')+data.content.url

    producer = ContentProducer(data.content)
    streaming = data.endpoint_model.result.type == ResultType.BinaryFile

    if data.endpoint_model.protocol.http_method.value == 'GET':
        if producer.has_content:
            raise ValueError(f"Cannot make a GET request: json or files are not empty.\nJson: {','.join(data.content.json)}\nFiles: {','.join(data.content.files)}")
        response = requests.get(url, stream=streaming)
    else:
        if producer.has_content:
            response = requests.post(url, data=producer.produce(), headers={'Content-Type': producer.content_type}, stream=streaming)
        else:
            response = requests.post(url, stream=streaming)

    if response.status_code != 200:
        raise ApiError(response)

    if data.endpoint_model.result.type == ResultType.BinaryFile:
        return response.iter_content(chunk_size=None), None

    ctx = SerializationContext()
    raw = response.json()
    result = data.endpoint_model.result.serializer.from_json(raw, ctx)
    return result, raw

