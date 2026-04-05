import ast
import inspect
import textwrap
import functools
from enum import Enum
from dataclasses import dataclass


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"

_ENDPOINT_ATTR = '_endpoint_attributes'


@dataclass
class EndpointAttributes:
    method: HttpMethod = HttpMethod.POST
    content_type: str | None = None
    verify_abstract: bool = True
    is_websocket: bool = False
    force_json_params: bool = False
    is_pathlike: str | None = None


def _is_stub_body(f) -> str|None:
    try:
        src = textwrap.dedent(inspect.getsource(f))
    except OSError:
        return None  # source not available, skip verification
    try:
        tree = ast.parse(src)
        func_def = tree.body[0]
        if not isinstance(func_def, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return "No function def"
        body = func_def.body
        # skip docstring
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body = body[1:]
        if len(body) == 1:
            stmt = body[0]
            if isinstance(stmt, ast.Pass):
                return None
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
                return None
            return str(stmt)
    except Exception as e:
        return str(e)



def _build_decorator(attrs: EndpointAttributes):
    def decorator(f):
        if attrs.verify_abstract:
            stub_status = _is_stub_body(f)
            if stub_status is not None:
                raise TypeError(
                    f"Endpoint '{f.__name__}' has verify_abstract=True but body is not '...' or 'pass'."
                    f"Use verify_abstract=False if the method has a real body."
                    f"Error is:\n{stub_status}"
                )
            def stub(*args, **kwargs):
                raise NotImplementedError(f"'{f.__name__}' is an abstract endpoint stub")
            functools.update_wrapper(stub, f)
            stub.__signature__ = inspect.signature(f)
            setattr(stub, _ENDPOINT_ATTR, attrs)
            return stub
        setattr(f, _ENDPOINT_ATTR, attrs)
        return f
    return decorator


def endpoint(func=None, method: str | HttpMethod = HttpMethod.POST, content_type: str | None = None, verify_abstract: bool = True, force_json_params: bool = False, is_pathlike: str | None = None):
    if isinstance(method, str):
        method = HttpMethod(method)
    attrs = EndpointAttributes(method=method, content_type=content_type, verify_abstract=verify_abstract, force_json_params=force_json_params, is_pathlike=is_pathlike)
    decorator = _build_decorator(attrs)
    if func is not None:
        return decorator(func)
    return decorator


def websocket(func=None, content_type: str | None = None, verify_abstract: bool = True):
    """Marks a method as a WebSocket endpoint."""
    attrs = EndpointAttributes(content_type=content_type, verify_abstract=verify_abstract, is_websocket=True)
    decorator = _build_decorator(attrs)
    if func is not None:
        return decorator(func)
    return decorator
