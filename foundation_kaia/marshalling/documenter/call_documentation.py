from dataclasses import dataclass
from ..protocol import CallModel, FileLikeHandler, File
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
        params = call.endpoint_model.params
        files = {}
        for param in params.file_params:
            raw = call.content.raw_values[param.name]
            files[param.name] = File(FileLikeHandler.guess_name(raw), FileLikeHandler.to_bytes(raw))
        if params.binary_stream_param is not None:
            name = params.binary_stream_param.name
            files[name] = File(name, FileLikeHandler.to_bytes(call.content.raw_values[name]))
        return RequestDocumentation(url=url, json=call.content.json_values, files=files)


@dataclass
class CallDocumentation:
    request: RequestDocumentation
    response: ResponseDocumentation
