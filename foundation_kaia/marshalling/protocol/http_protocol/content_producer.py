CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_BINARY_FILE = 'application/octet-stream'
CONTENT_TYPE_MULTIPART = 'multipart/form-data'
JSON_PARAMETERS_NAME = 'json_arguments'
from ..model import ContentModel, FileLikeHandler, EndpointModel
import json
from typing import Iterable


class ContentProducer:
    def __init__(self, content: ContentModel, endpoint: EndpointModel):
        self.content = content
        self.params = endpoint.params

    @property
    def has_content(self):
        return bool(self.params.json_params or self.params.file_params or self.params.binary_stream_param is not None)

    @property
    def content_type(self) -> str | None:
        if not self.has_content:
            return None
        if self.params.binary_stream_param is not None:
            return CONTENT_TYPE_BINARY_FILE
        if len(self.params.file_params) == 1 and not self.params.json_params:
            return CONTENT_TYPE_BINARY_FILE
        if self.params.json_params and not self.params.file_params:
            return CONTENT_TYPE_JSON
        return f'{CONTENT_TYPE_MULTIPART}; boundary={self.content.boundary}'

    def produce(self) -> Iterable[bytes]:
        if self.params.binary_stream_param is not None:
            yield from self.content.raw_values[self.params.binary_stream_param.name]

        elif len(self.params.file_params) == 1 and not self.params.json_params:
            name = self.params.file_params[0].name
            yield from FileLikeHandler.to_bytes_iterable(self.content.raw_values[name])

        elif self.params.json_params and not self.params.file_params:
            yield json.dumps(self.content.json_values).encode()

        else:  # multipart/form-data
            boundary_bytes = self.content.boundary.encode()
            if self.content.json_values:
                yield b'--' + boundary_bytes + b'\r\n'
                yield f'Content-Disposition: form-data; name="{JSON_PARAMETERS_NAME}"\r\n'.encode()
                yield b'Content-Type: application/json\r\n\r\n'
                yield json.dumps(self.content.json_values).encode()
                yield b'\r\n'
            for param in self.params.file_params:
                name = param.name
                yield b'--' + boundary_bytes + b'\r\n'
                yield f'Content-Disposition: form-data; name="{name}"; filename="{name}"\r\n'.encode()
                yield f'Content-Type: {CONTENT_TYPE_BINARY_FILE}\r\n\r\n'.encode()
                yield from FileLikeHandler.to_bytes_iterable(self.content.raw_values[name])
                yield b'\r\n'
            yield b'--' + boundary_bytes + b'--\r\n'
