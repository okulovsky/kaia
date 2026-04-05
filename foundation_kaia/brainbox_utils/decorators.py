from ..marshalling_2.marshalling.model.endpoint_decorator import _build_decorator, EndpointAttributes

def brainbox_endpoint(func=None, content_type: str | None = None):
    attrs = EndpointAttributes(content_type=content_type, verify_abstract=True, force_json_params=True)
    decorator = _build_decorator(attrs)
    if func is not None:
        return decorator(func)
    return decorator

def brainbox_websocket(func=None, content_type: str | None = None):
    attrs = EndpointAttributes(content_type=content_type, verify_abstract=True, is_websocket=True)
    decorator = _build_decorator(attrs)
    if func is not None:
        return decorator(func)
    return decorator