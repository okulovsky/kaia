from functools import wraps
from dataclasses import dataclass


@dataclass
class EndpointMetadata:
    url: str|None
    method: str
    json_pickle_result: bool


def endpoint(
        *,
        url: str|None = None,
        method = 'POST',
        json_pickle_result: bool = False
    ):
    def decorator(func):
        # Add the metadata as an attribute of the function
        func._metadata = EndpointMetadata(url, method, json_pickle_result)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator