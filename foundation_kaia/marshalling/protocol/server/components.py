from abc import ABC, abstractmethod
from typing import Callable
from ..model import EndpointModel, EndpointRegistrationData
from ..model.endpoint_model import ProtocolType
from ..model.service_model import ServiceModel
from ..http_protocol.http_server_endpoint import http_endpoint, build_route_path
from ..websocket_protocol.ws_server_endpoint import ws_endpoint


class IComponent(ABC):
    @abstractmethod
    def mount(self, app):
        pass


class EndpointComponent(IComponent):
    def __init__(self, method: Callable, model: EndpointModel | None = None, prefix: str|None = None):
        self.method = method
        self.model = model if model is not None else EndpointModel.parse(method)
        self.prefix = prefix

    def mount(self, app):
        model = self.model

        # Determine the callable: for bound methods use __self__ as service object,
        # for plain functions use the method directly.
        if hasattr(self.method, '__self__'):
            service = self.method.__self__
            callable_ = lambda **kw: getattr(service, model.signature.name)(**kw)
        else:
            callable_ = self.method

        registration = EndpointRegistrationData(endpoint=model, service=callable_)
        if self.prefix:
            route = build_route_path(model, address=self.prefix.strip('/') + '/' + model.name)
        else:
            route = build_route_path(model)

        if model.protocol.type == ProtocolType.HTTP:
            handler = http_endpoint(registration)
            methods = [model.protocol.http_method.value]
            app.add_api_route(route, handler, methods=methods, name=model.name)
        elif model.protocol.type == ProtocolType.WebSockets:
            handler = ws_endpoint(registration)
            app.add_api_websocket_route(route, handler, name=model.name)
        else:
            raise NotImplementedError(f"Protocol {model.protocol.type} is not supported")


class ServiceComponent(IComponent):
    """Mounts all @endpoint methods found on a @service-decorated class."""

    def __init__(self, service, prefix: str|None = None):
        self.service = service
        self.prefix = prefix

    def mount(self, app):
        service_model = ServiceModel.parse(self.service)
        for ep in service_model.endpoints:
            method = getattr(self.service, ep.signature.name)
            EndpointComponent(method, model=ep, prefix=self.prefix).mount(app)
