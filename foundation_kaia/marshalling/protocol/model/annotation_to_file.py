from ...reflector import DeclaredType, Annotation
from collections.abc import Iterable
from enum import Enum
from dataclasses import dataclass
from io import BytesIO
from .file import File
from pathlib import Path


class AnnotationToFileKind(Enum):
    NotFile = 0
    SimpleFile = 1
    BinaryStream = 2
    StringStream = 3
    CustomStream = 4


@dataclass
class AnnotationToFile:
    kind: AnnotationToFileKind
    custom_stream_item: Annotation | None = None  # set only for CustomStream

    @staticmethod
    def _detect_stream(declared_type: DeclaredType) -> 'AnnotationToFile|None':
        mro = declared_type.mro[0]
        if mro.type is Iterable:
            if len(mro.parameters) == 0:
                raise ValueError("Iterable must have exactly one parameter to be used in annotation for an endpoint")
            if len(mro.parameters) > 1:
                raise ValueError("Iterable is expected to have exactly one parameter")
            gpv = mro.parameters[0].generic_parameter_value
            if gpv.types and gpv.types[0].mro[0].type is bytes:
                return AnnotationToFile(AnnotationToFileKind.BinaryStream, None)
            elif gpv.types and gpv.types[0].mro[0].type is str:
                return AnnotationToFile(AnnotationToFileKind.StringStream, gpv)
            else:
                return AnnotationToFile(AnnotationToFileKind.CustomStream, gpv)
        return None

    @staticmethod
    def parse(annotation: Annotation) -> 'AnnotationToFile':
        annotation_to_file: AnnotationToFile | None = None
        has_file_type_main = False
        others = []
        for tp in annotation:
            atf = AnnotationToFile._detect_stream(tp)
            if atf is not None:
                if annotation_to_file is None:
                    annotation_to_file = atf
                else:
                    raise ValueError("Only one Iterable may appear in annotation")
            elif tp.mro[0].type is bytes or tp.mro[0].type is BytesIO or tp.mro[0].type is File:
                has_file_type_main = True
            else:
                others.append(tp)

        if annotation_to_file is not None and annotation_to_file.kind != AnnotationToFileKind.BinaryStream:
            if has_file_type_main:
                raise ValueError("Iterable[T]/Iterable[str] is incompatible with file-like types (bytes, BytesIO, File)")
            else:
                return annotation_to_file

        if not annotation_to_file and not has_file_type_main:
            return AnnotationToFile(AnnotationToFileKind.NotFile)

        for t in others:
            m = t.mro[0].type
            if m is str or m is Path:
                continue
            else:
                raise ValueError(f"Iterable[bytes]/BytesIO/bytes/File are only compatible with str or Path, but was {m}")

        if annotation_to_file is not None:
            return annotation_to_file
        return AnnotationToFile(AnnotationToFileKind.SimpleFile, None)
