from dataclasses import dataclass
from .endpoint_documentation import EndpointDocumentation
from ..protocol import ServiceModel


@dataclass
class ServiceDocumentation:
    name: str
    docstring: str | None
    endpoints: dict[str, EndpointDocumentation]

    @staticmethod
    def parse(interface: type) -> 'ServiceDocumentation':
        model = ServiceModel.parse(interface)
        endpoints = {
            ep.signature.name: EndpointDocumentation.parse(ep)
            for ep in model.endpoints
        }
        return ServiceDocumentation(
            name=model.name,
            docstring=interface.__doc__,
            endpoints=endpoints,
        )
