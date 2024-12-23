from functools import wraps
from dataclasses import dataclass


@dataclass
class EndpointMetadata:
    url: str|None
    method: str


def endpoint(
        *,
        url: str|None = None,
        method = 'POST',
    ):
    def decorator(func):
        # Add the metadata as an attribute of the function
        func._metadata = EndpointMetadata(url, method)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator