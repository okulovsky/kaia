from dataclasses import dataclass
from ..marshalling.model.call_model import CallModel
from ..marshalling.model.file_like import FileLikeHandler
from ..marshalling.model.file import File
from ..serialization import JSON


@dataclass
class ResponseDocumentation:
    json: JSON | None
    file: File | None
    error: str | None


@dataclass
class RequestDocumentation:
    url: str
    json: JSON
    files: dict[str, File]

    @staticmethod
    def parse(call: CallModel) -> 'RequestDocumentation':
        url = call.base_url + call.content.url
        files = {
            name: File(FileLikeHandler.guess_name(f), FileLikeHandler.to_bytes(f))
            for name, f in call.content.files.items()
        }
        if call.content.binary_stream is not None:
            name = call.content.binary_stream.name
            files[name] = File(name, FileLikeHandler.to_bytes(call.content.binary_stream.iterable))
        return RequestDocumentation(url=url, json=call.content.json, files=files)


@dataclass
class CallDocumentation:
    request: RequestDocumentation
    response: ResponseDocumentation
