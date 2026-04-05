import re
from dataclasses import dataclass
from typing import Any
from ...reflector import DeclaredType
from .endpoint_model import EndpointModel
from .endpoint_decorator import _ENDPOINT_ATTR

_SERVICE_ATTR = '_service_attributes'


@dataclass
class ServiceAttributes:
    name: str


def convert_name(s: str) -> str:
    # Remove leading I if followed by uppercase (e.g. IService -> Service)
    if len(s) > 1 and s[0] == 'I' and s[1].isupper():
        s = s[1:]
    # Remove trailing Interface
    if s.endswith('Interface'):
        s = s[:-len('Interface')]
    # Convert CamelCase to kebab-case
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '-', s)
    return s.lower()


def service(cls=None):
    def decorator(c):
        n = convert_name(c.__name__)
        setattr(c, _SERVICE_ATTR, ServiceAttributes(n))
        return c
    if cls is not None:
        return decorator(cls)
    return decorator


@dataclass
class ServiceModel:
    name: str
    endpoints: tuple[EndpointModel, ...]

    @staticmethod
    def parse(value: Any) -> 'ServiceModel':
        desc = DeclaredType.parse(value)

        # Collect all @service-decorated ancestors in MRO order.
        # The first one (most-derived) determines the service name.
        service_entries = [entry for entry in desc.mro if _SERVICE_ATTR in entry.type.__dict__]
        if not service_entries:
            raise TypeError(
                f"Type '{desc.mro[0].type.__name__}' and none of its bases are decorated with @service"
            )

        attrs: ServiceAttributes = getattr(service_entries[0].type, _SERVICE_ATTR)

        # Gather endpoints from every @service ancestor.  seen_names ensures that
        # when a child interface re-declares an endpoint that a parent also declares,
        # the child's version (encountered first) wins — same semantics as Python MRO.
        endpoints = []
        seen_names: set[str] = set()
        for entry in service_entries:
            actual_cls = entry.type
            type_map = entry.type_map
            for name, member in vars(actual_cls).items():
                if name in seen_names:
                    continue
                func = member
                if isinstance(member, (classmethod, staticmethod)):
                    func = member.__func__
                if not callable(func):
                    continue
                if not hasattr(func, _ENDPOINT_ATTR):
                    continue
                # Always parse the interface member (which carries _ENDPOINT_ATTR and the
                # correct signature).  When value is a service *instance*, getattr(value, name)
                # returns the concrete override which has no _ENDPOINT_ATTR, so EndpointModel.parse
                # would return None and the route would never be registered.
                # The actual callable is resolved later in ServiceComponent via getattr(service, name).
                ep = EndpointModel.parse(member, type_map=type_map)
                if ep is not None:
                    endpoints.append(ep)
                    seen_names.add(name)

        service_model = ServiceModel(name=attrs.name, endpoints=tuple(endpoints))
        for e in service_model.endpoints:
            e.service_model = service_model
        return service_model
