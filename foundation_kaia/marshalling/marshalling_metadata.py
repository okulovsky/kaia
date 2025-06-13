from typing import *
from dataclasses import dataclass
from .signature_processor import SignatureProcessor
from .endpoint import EndpointMetadata

@dataclass
class MarshallingMetadata:
    name: str
    method: Callable
    endpoint: EndpointMetadata
    signature: SignatureProcessor

    def get_endpoint_address(self):
        if self.endpoint.url is None:
            return '/'+self.name
        return self.endpoint.url

    @staticmethod
    def _get_endpoints(_obj, _type) -> tuple['MarshallingMetadata',...]:
        result = []
        for attr_name, attr_value in _type.__dict__.items():
            if not hasattr(attr_value,'_metadata'):
                continue
            result.append(MarshallingMetadata(
                attr_name,
                getattr(_obj, attr_name) if _obj is not None else None,
                attr_value._metadata,
                SignatureProcessor.from_signature(attr_value)
            ))
        return tuple(result)

    @staticmethod
    def get_endpoints_from_object(obj) -> tuple['MarshallingMetadata',...]:
        return MarshallingMetadata._get_endpoints(obj, type(obj))

    @staticmethod
    def get_endpoints_from_type(type: Type) -> tuple['MarshallingMetadata',...]:
        return MarshallingMetadata._get_endpoints(None, type)