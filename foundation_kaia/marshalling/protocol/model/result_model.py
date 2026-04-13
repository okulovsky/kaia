from dataclasses import dataclass
from enum import Enum
from ...reflector import Signature
from ...serialization import Serializer
from .annotation_to_file import AnnotationToFile, AnnotationToFileKind
from mimetypes import guess_extension as _mimetypes_guess_extension

_KNOWN_EXTENSIONS = {
    'audio/wav': '.wav',
    'audio/mp3': '.mp3',
    'audio/mpeg': '.mp3',
    'audio/ogg': '.ogg',
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/bmp': '.bmp',
    'application/json': '.json',
    'text/plain': '.txt',
}


class ResultType(Enum):
    Json = 0
    BinaryFile = 1
    CustomIterable = 2
    StringIterable = 3


@dataclass
class ResultModel:
    type: ResultType
    serializer: Serializer | None   # None for BinaryFile; result serializer for Json; item serializer for CustomIterable/StringIterable
    content_type: str

    def guess_extension(self):
        if self.content_type in _KNOWN_EXTENSIONS:
            return _KNOWN_EXTENSIONS[self.content_type]
        ext = _mimetypes_guess_extension(self.content_type)
        return ext or ''

    @staticmethod
    def parse(signature: Signature, content_type: str | None = None):
        atf = AnnotationToFile.parse(signature.returned_type)
        if atf.kind in (AnnotationToFileKind.BinaryStream, AnnotationToFileKind.SimpleFile):
            return ResultModel(
                ResultType.BinaryFile,
                None,
                content_type or 'application/octet-stream'
            )
        if atf.kind == AnnotationToFileKind.StringStream:
            return ResultModel(
                ResultType.StringIterable,
                Serializer(atf.custom_stream_item),
                content_type or 'text/plain'
            )
        if atf.kind == AnnotationToFileKind.CustomStream:
            return ResultModel(
                ResultType.CustomIterable,
                Serializer(atf.custom_stream_item),
                content_type or 'application/jsonlines+json'
            )
        return ResultModel(
            ResultType.Json,
            Serializer(signature.returned_type),
            content_type or 'application/json'
        )
