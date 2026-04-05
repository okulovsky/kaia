from typing import Iterable
from .content_producer import CONTENT_TYPE_BINARY_FILE, CONTENT_TYPE_MULTIPART, CONTENT_TYPE_JSON, CONTENT_TYPE_BINARY_STREAM
from ..model import EndpointModel
import json
from email.parser import BytesParser
from ..model import parse_json


def parse_content(kwargs: dict, content_type: str, body: Iterable[bytes], model: EndpointModel) -> None:
    if content_type == CONTENT_TYPE_JSON:
        raw = json.loads(b''.join(body))
        parse_json(kwargs, raw, model.params.json_params)

    elif content_type == CONTENT_TYPE_BINARY_FILE:
        kwargs[model.params.file_params[0].name] = b''.join(body)

    elif content_type == CONTENT_TYPE_BINARY_STREAM:
        kwargs[model.params.binary_stream_param.name] = body

    elif content_type.startswith(CONTENT_TYPE_MULTIPART):
        raw = b''.join(body)
        msg = BytesParser().parsebytes(
            f'Content-Type: {content_type}\r\n\r\n'.encode() + raw
        )
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            name = part.get_param('name', header='content-disposition')
            part_ct = part.get_content_type()
            data = part.get_payload(decode=True)
            if part_ct == CONTENT_TYPE_JSON:
                json_body = json.loads(data) if data else {}
                parse_json(kwargs, json_body, model.params.json_params)
            else:
                kwargs[name] = data
