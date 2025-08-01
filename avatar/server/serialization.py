from typing import *
from datetime import datetime
from enum import Enum
import jsonpickle
import json
from dataclasses import is_dataclass, fields
import importlib
import builtins
import types

def _unwrap_optional(tp: type) -> type:
    """
    If `tp` is of the form Optional[X] or X | None, return X.
    Otherwise, return tp unchanged.
    """
    origin = get_origin(tp)
    # typing.Optional is just Union[X, None]
    # Python 3.10+: X | None has origin types.UnionType
    if origin is Union or origin is types.UnionType:
        args = get_args(tp)
        # filter out NoneType
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return tp

def _is_primitive(_type: Type):
    if _type in (str, int, float, bool, tuple, datetime):
        return True
    if get_origin(_type) is tuple:
        return True
    try:
        if issubclass(_type, Enum):
            return True
    except:
        pass
    return False

def to_json(value: Any, _type: Type|None) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, tuple):
        return [to_json(v, None) for v in value]
    if isinstance(value, dict):
        return {k: to_json(v, None) for k, v in value.items()}
    if isinstance(value, list):
        return [to_json(v, None) for v in value]
    if _type is not None and is_dataclass(_type):
        result = {}
        for field_info in fields(_type):
            field_type = field_info.type if field_info.metadata.get('json', False) else None
            result[field_info.name] = to_json(getattr(value, field_info.name), field_type)
        return result
    return json.loads(jsonpickle.encode(value))


def from_json(value: Any, _type: Type|None, path='/'):
    if value is None:
        return None
    if isinstance(value, dict) and 'py/object' in value:
        return jsonpickle.decode(json.dumps(value))
    if _type is None:
        return value
    if _type in (str, int, float, bool):
        if not isinstance(value, _type):
            raise ValueError(f"Deserialization error at path {path}: type {_type} is expected, but the value was {value}")
        return value
    if issubclass(_type, Enum):
        if not isinstance(value, str):
            raise ValueError(f"Deserialization error at path {path}: enum {_type} is expected, but the value was {value}")
        if value not in _type.__members__:
            raise ValueError(f"Deserialization error at path {path}: value {value} is not a member of enum {_type}")
        return _type[value]
    if _type is tuple or get_origin(_type) is tuple:
        if not isinstance(value, list):
            raise ValueError(f"Deserialization error at path {path}: tuple is expected, but the value is not list - {value}")
        return tuple(from_json(element, None) for element in value)
    if isinstance(value, list):
        if not isinstance(value, list):
            raise ValueError(f"Deserialization error at path {path}: list is expected, but the value is not list - {value}")
        return [from_json(element, None) for element in value]
    if isinstance(value, dict):
        if _type is dict:
            return value
        if is_dataclass(_type):
            inst = object.__new__(_type)
            for field_info in fields(_type):
                field_type = _unwrap_optional(field_info.type)
                field_value = value.get(field_info.name, None)
                field_path = path+field_info.name+"/"
                if field_type is not None:
                    if not _is_primitive(field_type) and not field_info.metadata.get('json', False):
                        field_type = None
                if field_value is not None:
                    field_value = from_json(field_value, field_type, field_path)
                setattr(inst, field_info.name, field_value)
            return inst
        else:
            raise ValueError(f"Expected _type {_type}, but was dictionary")
    return value


def get_type_by_full_name(full_name: str) -> Type[Any]:
    module_name, type_name = full_name.rsplit('/')
    module = importlib.import_module(module_name)
    try:
        return getattr(module, type_name)
    except AttributeError:
        raise ImportError(f"Module '{module_name}' has no attribute '{type_name}'")

def get_full_name_by_type(_type: Type) -> str:
    return _type.__module__ + '/' + _type.__qualname__