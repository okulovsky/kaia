from typing import Iterable
from ..model import EndpointModel
import json
from email.parser import BytesParser
from ..model import parse_json
from .content_producer import JSON_PARAMETERS_NAME

CONTENT_TYPE_BINARY_FILE = 'application/octet-stream'


def parse_content(kwargs: dict, body: Iterable[bytes], model: EndpointModel, content_type: str = '') -> None:
    """Parse the request body into kwargs, branching on model.params structure.

    content_type is only needed for multipart requests (to extract the boundary).
    """
    params = model.params

    if params.binary_stream_param is not None:
        kwargs[params.binary_stream_param.name] = body

    elif len(params.file_params) == 1 and not params.json_params:
        kwargs[params.file_params[0].name] = b''.join(body)

    elif params.json_params and not params.file_params:
        raw = json.loads(b''.join(body))
        parse_json(kwargs, raw, params.json_params)

    else:  # multipart: multiple files, or json + files
        _parse_multipart(kwargs, content_type, b''.join(body), model)


def _parse_multipart(kwargs: dict, content_type: str, raw: bytes, model: EndpointModel) -> None:
    msg = BytesParser().parsebytes(
        f'Content-Type: {content_type}\r\n\r\n'.encode() + raw
    )
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        name = part.get_param('name', header='content-disposition')
        part_ct = part.get_content_type()
        data = part.get_payload(decode=True)
        if name == JSON_PARAMETERS_NAME:
            json_body = json.loads(data) if data else {}
            parse_json(kwargs, json_body, model.params.json_params)
        else:
            kwargs[name] = data
