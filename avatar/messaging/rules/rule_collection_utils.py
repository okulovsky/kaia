import collections.abc
from typing import *
from typing import _GenericAlias
import types
import inspect
from ..stream import IMessage
from .rule import Rule

def get_single_argument_type(handler):
    import inspect
    sig = inspect.signature(handler)
    params = list(sig.parameters.values())

    # Ensure exactly one remaining argument
    if len(params) != 1:
        raise ValueError("Callable must have exactly one argument (excluding self/cls)")

    param = params[0]
    annotation = param.annotation

    if annotation == inspect._empty:
        return None

    if not isinstance(annotation, type):
        annotation = get_origin(annotation)

    if not isinstance(annotation, type):
        raise ValueError(f"Annotation must be type, but was {annotation}")
    return annotation


def unroll_output_type(tp) -> list:
    origin = get_origin(tp)
    args = get_args(tp)

    if origin in [tuple, Tuple, Union, types.UnionType, collections.abc.Iterable]:
        result = []
        for arg in args:
            result.extend(unroll_output_type(arg))
        return result

    if tp is Ellipsis or tp is None:
        return []
    if origin is None:
        return [tp]
    return [origin]



def get_annotated_output_type(handler):
    sig = inspect.signature(handler)
    ret = sig.return_annotation

    if ret is inspect.Signature.empty:
        return None

    result = unroll_output_type(ret)
    if len(result) == 0:
        return None
    return result