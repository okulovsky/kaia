CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_BINARY_FILE = 'application/octet-stream'
CONTENT_TYPE_BINARY_STREAM = 'application/x-binary-stream'
CONTENT_TYPE_MULTIPART = 'multipart/form-data'
from ..model import ContentModel, FileLikeHandler
import json
from typing import Iterable



class ContentProducer:
    def __init__(self, model: ContentModel):
        self.model = model

    @property
    def has_content(self):
        return len(self.model.files) > 0 or len(self.model.json) > 0 or self.model.binary_stream is not None

    @property
    def content_type(self) -> str|None:
        if not self.has_content:
            return None
        if len(self.model.json) == 0 and len(self.model.files) == 0:
            return CONTENT_TYPE_BINARY_STREAM
        if len(self.model.json) == 0 and len(self.model.files) == 1 and self.model.binary_stream is None:
            return CONTENT_TYPE_BINARY_FILE
        if len(self.model.json) > 0 and len(self.model.files) == 0 and self.model.binary_stream is None:
            return CONTENT_TYPE_JSON
        return f'{CONTENT_TYPE_MULTIPART}; boundary={self.model.boundary}'


    def produce(self) -> Iterable[bytes]:
        ct = self.content_type

        if ct == CONTENT_TYPE_JSON:
            yield json.dumps(self.model.json).encode()

        elif ct == CONTENT_TYPE_BINARY_FILE:
            yield from FileLikeHandler.to_bytes_iterable(next(iter(self.model.files.values())))

        elif ct == CONTENT_TYPE_BINARY_STREAM:
            yield from self.model.binary_stream.iterable

        else:  # multipart/form-data
            boundary_bytes = self.model.boundary.encode()
            if len(self.model.json) > 0:
                yield b'--' + boundary_bytes + b'\r\n'
                yield b'Content-Disposition: form-data; name="payload"\r\n'
                yield b'Content-Type: application/json\r\n\r\n'
                yield json.dumps(self.model.json).encode()
                yield b'\r\n'
            for name in self.model.files:
                yield b'--' + boundary_bytes + b'\r\n'
                yield f'Content-Disposition: form-data; name="{name}"; filename="{name}"\r\n'.encode()
                yield f'Content-Type: {CONTENT_TYPE_BINARY_FILE}\r\n\r\n'.encode()
                yield from FileLikeHandler.to_bytes_iterable(self.model.files[name])
                yield b'\r\n'
            yield b'--' + boundary_bytes + b'--\r\n'
