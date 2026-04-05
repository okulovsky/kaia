from __future__ import annotations
from ...reflector import Signature
from dataclasses import dataclass
from typing import TypeVar, TYPE_CHECKING
from .endpoint_decorator import EndpointAttributes, _ENDPOINT_ATTR
from .params_model import ParamsModel
from .result_model import ResultModel, ResultType
from .protocol_model import ProtocolModel, ProtocolType

if TYPE_CHECKING:
    from .service_model import ServiceModel


@dataclass
class EndpointModel:
    name: str
    signature: Signature
    protocol: ProtocolModel
    params: ParamsModel
    result: ResultModel
    
    service_model: ServiceModel|None = None

    @property
    def endpoint_address(self) -> str:
        if self.service_model is not None:
            return f"{self.service_model.name}/{self.name}"
        return self.name

    @staticmethod
    def parse(method, type_map: dict[TypeVar, type] | None = None) -> 'EndpointModel | None':
        # Unwrap classmethod/staticmethod wrappers to get the raw function
        func = method
        if isinstance(method, (classmethod, staticmethod)):
            func = method.__func__
        elif hasattr(method, '__func__'):
            func = method.__func__

        attrs: EndpointAttributes | None = getattr(func, _ENDPOINT_ATTR, None)
        if attrs is None:
            return None

        sig = Signature.parse(method, type_map=type_map)

        unresolved = [
            arg for arg in sig.arguments
            if arg.annotation.from_typevar is not None and arg.annotation.raw_annotation is object
        ]
        if unresolved:
            names = ', '.join(
                f"'{arg.name}: {arg.annotation.from_typevar.__name__}'" for arg in unresolved
            )
            raise TypeError(
                f"Endpoint '{sig.name}': unbound type parameters in arguments {names}. "
                f"Pass the service instance with concrete type arguments, "
                f"e.g. MyService[ConcreteType](...)."
            )

        protocol = ProtocolModel(
            type=ProtocolType.WebSockets if attrs.is_websocket else ProtocolType.HTTP,
            http_method=None if attrs.is_websocket else attrs.method,
        )

        params_model = ParamsModel.parse(sig, protocol, force_json_params=attrs.force_json_params, is_pathlike=attrs.is_pathlike)
        result_model = ResultModel.parse(sig, attrs.content_type)

        _STREAMING_RESULT = (ResultType.BinaryFile, ResultType.CustomIterable)
        has_stream_input = (
            params_model.binary_stream_param is not None
            or params_model.custom_stream_param is not None
        )
        if protocol.type == ProtocolType.HTTP and has_stream_input and result_model.type in _STREAMING_RESULT:
            stream_name = (
                params_model.binary_stream_param.name
                if params_model.binary_stream_param is not None
                else params_model.custom_stream_param.name
            )
            raise ValueError(
                f"HTTP endpoint '{sig.name}': streaming input ('{stream_name}') cannot be combined "
                f"with streaming output. Use WebSockets instead."
            )

        return EndpointModel(
            name = sig.name.replace('_','-'),
            signature=sig,
            protocol=protocol,
            params=params_model,
            result=result_model,
        )
