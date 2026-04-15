from typing import Any, Iterable
from ..model import EndpointModel, CallModel, ServiceModel
from ..model.endpoint_model import ProtocolType
from ..http_protocol import http_api_call
from ..websocket_protocol import ws_api_call


class ApiCall:
    def __init__(self, base_url: str, model: EndpointModel, custom_prefix: str | None = None):
        self.endpoint = model
        address = custom_prefix.strip('/') + '/' + model.name if custom_prefix is not None else None
        self.call_model_factory = CallModel.Factory(base_url, model, address)
        self.last_request: CallModel|None = None
        self.last_response: Any = None
        self.last_raw_response: Any = None

    def create_content_model(self, *args, **kwargs) -> CallModel:
        return self.call_model_factory(*args, **kwargs)

    def make_call(self, model: CallModel) -> Any:
        self.last_request = model
        self.last_response = None
        self.last_raw_response = None
        protocol = self.endpoint.protocol.type
        if protocol == ProtocolType.HTTP:
            self.last_response, self.last_raw_response = http_api_call(self.last_request)
        elif protocol == ProtocolType.WebSockets:
            self.last_response, self.last_raw_response = ws_api_call(self.last_request)
        else:
            raise NotImplementedError(f"Protocol {protocol} is not supported")
        return self.last_response

    def __call__(self, *args, **kwargs) -> Any:
        return self.make_call(self.create_content_model(*args, **kwargs))

    @staticmethod
    def iterate_endpoints(base_url: str, interface, custom_prefix: str | None = None) -> Iterable[tuple[str, 'ApiCall']]:
        """Yield (name, ApiCall) for every @endpoint method found on `interface`."""
        service_model = ServiceModel.parse(interface)
        for ep in service_model.endpoints:
            yield ep.signature.name, ApiCall(base_url, ep, custom_prefix)

    @staticmethod
    def define_endpoints(obj, base_url: str, interface, custom_prefix: str | None = None) -> None:
        """Set an ApiCall attribute on `obj` for every @endpoint found on `interface`."""
        for name, call in ApiCall.iterate_endpoints(base_url, interface, custom_prefix):
            setattr(obj, name, call)



