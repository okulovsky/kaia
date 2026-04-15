from typing import Any
from ...serialization import SerializationContext
from ..model import ParamDefinition
from ..model import EndpointModel

def parse_json(kwargs: dict, raw: Any, json_params: tuple[ParamDefinition,...]):
    ctx = SerializationContext()
    for param in json_params:
        if param.name in raw:
            with ctx.subpath(param.name):
                kwargs[param.name] = param.serializer.from_json(raw[param.name], ctx)


def parse_url(kwargs: dict, model: EndpointModel, path_params: dict, query_params: dict) -> None:
    ctx = SerializationContext()

    for param in model.params.path_params:
        raw = path_params.get(param.name)
        if raw is None:
            raise ValueError(f"Missing path parameter: {param.name}")
        with ctx.subpath(param.name):
            kwargs[param.name] = param.serializer.from_string(raw, ctx)

    if model.params.pathlike_param is not None:
        param = model.params.pathlike_param
        raw = path_params.get(param.name)
        if raw is None:
            raise ValueError(f"Missing path parameter: {param.name}")
        with ctx.subpath(param.name):
            kwargs[param.name] = param.serializer.from_string(raw, ctx)

    for param in model.params.query_params:
        raw = query_params.get(param.name, None)
        if raw is not None:
            kwargs[param.name] = param.serializer.from_string(raw, ctx)
        elif param.argument_description.default is None:
            kwargs[param.name] = None
