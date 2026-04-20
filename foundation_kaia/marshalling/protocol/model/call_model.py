from typing import Callable, Any
from .content_model import ContentModel
from ..model import EndpointModel
from dataclasses import dataclass


@dataclass
class CallModel:
    base_url: str
    endpoint_model: EndpointModel
    content: ContentModel

    def call_locally(self, function: Callable) -> Any:
        """Call ``function`` directly using the parameters captured in this CallModel,
        bypassing any HTTP/WebSocket transport layer."""
        # Lazy imports to avoid the circular: call_model → parse → model/__init__ → call_model
        from .parse import parse_json, parse_url
        kwargs: dict = {}
        model = self.endpoint_model

        # --- URL params (path + query) ---
        # ContentModel serialises them into the URL string; reconstruct the dicts.
        url = self.content.url           # e.g. "/service/endpoint/val1?q=v"
        prefix = f"/{model.endpoint_address}"
        remaining = url[len(prefix):]    # e.g. "/val1?q=v"

        path_part, _, query_part = remaining.partition('?')
        path_segments = [p for p in path_part.split('/') if p]

        path_params_dict = {
            param.name: path_segments[i]
            for i, param in enumerate(model.params.path_params)
            if i < len(path_segments)
        }
        query_params_dict = {}
        if query_part:
            for item in query_part.split('&'):
                k, _, v = item.partition('=')
                if k:
                    query_params_dict[k] = v

        parse_url(kwargs, model, path_params_dict, query_params_dict)

        # --- JSON params ---
        parse_json(kwargs, self.content.json_values, model.params.json_params)

        # --- File, binary stream, and custom stream params ---
        for name, value in self.content.raw_values.items():
            kwargs[name] = value

        return function(**kwargs)

    class Factory:
        def __init__(self, base_url: str, model: EndpointModel, address: str | None = None):
            self.base_url = base_url
            self.model = model
            self.address = address

        def __call__(self, *args, **kwargs) -> 'CallModel':
            values = self.model.signature.assign_parameters_to_names(*args, **kwargs)
            content = ContentModel.parse(values, self.model, self.address)
            content.base_url = self.base_url
            return CallModel(self.base_url, self.model, content)

        @staticmethod
        def test(function, type_map = None):
            model = EndpointModel.parse(function, type_map)
            return CallModel.Factory('http://127.0.0.1:8080', model)






