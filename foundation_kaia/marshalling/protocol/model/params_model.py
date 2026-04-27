from dataclasses import dataclass, field
from pathlib import Path
from ...reflector import Annotation, DeclaredType, FunctionArgumentDescription, Signature
from ...serialization import Serializer
from .protocol_model import ProtocolType, ProtocolModel, HttpMethod
from .annotation_to_file import AnnotationToFile, AnnotationToFileKind


@dataclass
class ParamDefinition:
    argument_description: FunctionArgumentDescription
    serializer: Serializer

    @property
    def name(self) -> str:
        return self.argument_description.name


@dataclass
class ParamsModel:
    path_params: tuple[ParamDefinition, ...]
    query_params: tuple[ParamDefinition, ...]
    json_params: tuple[ParamDefinition, ...]
    file_params: tuple[FunctionArgumentDescription,...]
    binary_stream_param: FunctionArgumentDescription|None
    custom_stream_param: ParamDefinition|None
    pathlike_param: ParamDefinition|None = None

    @staticmethod
    def parse(signature: Signature, protocol: ProtocolModel, force_json_params: bool = False, is_pathlike: str | None = None):
        path_params = []
        query_params = []
        json_params = []
        file_params = []
        binary_stream_param: FunctionArgumentDescription|None = None
        custom_stream_param: ParamDefinition|None = None
        pathlike_param: ParamDefinition|None = None

        for arg in signature.arguments:
            if arg.name == 'self':
                continue

            if is_pathlike is not None and arg.name == is_pathlike:
                _validate_pathlike_annotation(arg)
                serializer = Serializer(arg.annotation)
                pathlike_param = ParamDefinition(arg, serializer)
                continue

            atf = AnnotationToFile.parse(arg.annotation)

            if atf.kind in (AnnotationToFileKind.BinaryStream, AnnotationToFileKind.StringStream, AnnotationToFileKind.CustomStream):
                if binary_stream_param is not None:
                    raise ValueError(f"Only one parameter can be streaming, found two: {arg.name} and {binary_stream_param.name}")
                if custom_stream_param is not None:
                    raise ValueError(f"Only one parameter can be streaming, found two: {arg.name} and {custom_stream_param.name}")
                if atf.kind == AnnotationToFileKind.BinaryStream:
                    binary_stream_param = arg
                else:
                    item_serializer = Serializer(atf.custom_stream_item)
                    custom_stream_param = ParamDefinition(arg, item_serializer)
                continue

            if atf.kind == AnnotationToFileKind.SimpleFile:
                file_params.append(arg)
                continue

            serializer = Serializer(arg.annotation)

            if arg.annotation.from_typevar is not None:
                json_params.append(ParamDefinition(arg, serializer))
                continue

            if not force_json_params and serializer.is_primitive:
                path_params.append(ParamDefinition(arg, serializer))
                continue

            if not force_json_params and serializer.is_primitive_or_nullable:
                query_params.append(ParamDefinition(arg, serializer))
                continue

            json_params.append(ParamDefinition(arg, serializer))

        if protocol.type == ProtocolType.HTTP and binary_stream_param is not None and (json_params or file_params):
            raise ValueError(
                f"Stream parameter '{binary_stream_param}' cannot be combined with "
                f"json or file parameters in HTTP protocol. Stream must be the only body argument."
            )

        return ParamsModel(
            tuple(path_params),
            tuple(query_params),
            tuple(json_params),
            tuple(file_params),
            binary_stream_param,
            custom_stream_param,
            pathlike_param,
        )


def _validate_pathlike_annotation(arg: FunctionArgumentDescription) -> None:
    _VALID = (str, Path, type(None))
    for declared_type in arg.annotation:
        if declared_type.mro[0].type not in _VALID:
            raise ValueError(
                f"Parameter '{arg.name}' marked with is_pathlike must be annotated with "
                f"str or Path, got {declared_type.mro[0].type.__name__}"
            )
