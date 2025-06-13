from typing import *
from .marshalling_metadata import MarshallingMetadata
from .api_binding import ApiBinding
from .api_utils import ApiUtils

def bind_to_api(api_type: Type):
    def decorator(cls):
        metadata = MarshallingMetadata.get_endpoints_from_type(api_type)
        abs_methods = set(cls.__abstractmethods__)
        for meta in metadata:
            if meta.name not in abs_methods:
                raise ValueError(f"{meta.name} is present in API but absent/not marked as abstract in {api_type}")
            abs_methods.remove(meta.name)
        cls.__abstractmethods__ = frozenset(abs_methods)
        cls.__api_endpoints__ = metadata
        return cls
    return decorator


class Api:
    def __init__(self, address: str):
        ApiUtils.check_address(address)
        self.address = address

        for meta in type(self).__api_endpoints__:
            setattr(self, meta.name, ApiBinding(address, meta))


    def wait(self, max_time_in_seconds=10):
        ApiUtils.wait_for_reply(
            f'http://{self.address}/heartbeat',
            max_time_in_seconds,
        )








