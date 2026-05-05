import json
import uuid
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from ..model import ParamsModel
from ..model.file_like import FileLikeHandler
from ..model.file import File
from ...serialization import SerializationContext, Serializer
from dataclasses import dataclass, field
from typing import Any
from ..model import EndpointModel
from ..model import FileLike

_FILE_LIKE_TYPES = (str, Path, bytes, BytesIO, File)


@dataclass
class ContentModel:
    boundary: str
    url: str
    json_values: dict
    raw_values: dict

    @staticmethod
    def _build_url(values: dict, model: EndpointModel, address: str | None = None) -> str:
        ctx = SerializationContext()

        parts = [address if address is not None else model.endpoint_address]

        for param in model.params.path_params:
            value = values.get(param.name, param.argument_description.default)
            with ctx.subpath(param.name):
                parts.append(param.serializer.to_string(value, ctx))

        if model.params.pathlike_param is not None:
            param = model.params.pathlike_param
            value = values.get(param.name, param.argument_description.default)
            with ctx.subpath(param.name):
                parts.append(param.serializer.to_string(value, ctx))

        url = '/'.join(parts)

        query_parts = []
        for param in model.params.query_params:
            value = values.get(param.name, param.argument_description.default)
            if value is None:
                continue
            with ctx.subpath(param.name):
                query_parts.append(f"{param.name}={param.serializer.to_string(value, ctx)}")

        if len(query_parts) > 0:
            url += '?' + '&'.join(query_parts)

        return "/" + url

    @staticmethod
    def _build_json_values(values: dict, model: ParamsModel) -> dict:
        ctx = SerializationContext()
        body = {}
        for param in model.json_params:
            if param.name in values:
                with ctx.subpath(param.name):
                    body[param.name] = param.serializer.to_json(values[param.name], ctx)
        return body

    @staticmethod
    def _build_raw_values(values: dict, model: ParamsModel) -> dict:
        raw = {}
        for param in model.file_params:
            if param.name not in values:
                raise ValueError(f"FileLike param {param.name} has no value")
            value = values[param.name]
            if value is None:
                raise ValueError(f"FileLike param {param.name} has null value")
            raw[param.name] = value

        if model.binary_stream_param is not None:
            name = model.binary_stream_param.name
            if name not in values:
                raise ValueError(f"Stream param {name} has no value")
            value = values[name]
            if value is None:
                raise ValueError(f"Stream param {name} has null value")
            raw[name] = FileLikeHandler.to_bytes_iterable(value) if isinstance(value, _FILE_LIKE_TYPES) else value

        if model.custom_stream_param is not None:
            name = model.custom_stream_param.name
            if name not in values:
                raise ValueError(f"Custom stream param {name} has no value")
            value = values[name]
            if value is None:
                raise ValueError(f"Custom stream param {name} has null value")
            raw[name] = value

        return raw

    @staticmethod
    def parse(values: dict, model: EndpointModel, address: str | None = None):
        return ContentModel(
            uuid.uuid4().hex,
            ContentModel._build_url(values, model, address),
            ContentModel._build_json_values(values, model.params),
            ContentModel._build_raw_values(values, model.params),
        )
