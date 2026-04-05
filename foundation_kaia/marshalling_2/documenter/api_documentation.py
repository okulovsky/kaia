from dataclasses import dataclass, field
from .service_documentation import ServiceDocumentation
from ..marshalling.model.service_model import _SERVICE_ATTR
from ..reflector import DeclaredType


@dataclass
class ApiDocumentation:
    services: dict[str, ServiceDocumentation] = field(default_factory=dict)

    @staticmethod
    def parse(tp: type) -> 'ApiDocumentation':
        services = {}
        for entry in DeclaredType.parse(tp).mro:
            if _SERVICE_ATTR in entry.type.__dict__:
                resolved = entry.generic_type if entry.generic_type is not None else entry.type
                doc = ServiceDocumentation.parse(resolved)
                services[doc.name] = doc
        return ApiDocumentation(services=services)
