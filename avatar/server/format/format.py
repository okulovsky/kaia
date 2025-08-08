from typing import get_origin, get_args, Union, List, Tuple, Dict
import types
from .formatter import IFormatter, SerializationPath
from .default_formatter import DefaultFormatter
from .dataclass_formatter import DataClassFormatter
from .custom_formatters import ListFormatter, TupleFormatter, DictFormatter, DatetimeFormatter, EnumFormatter, PrimitiveFormatter, FloatFormatter
from enum import Enum
from dataclasses import is_dataclass
from datetime import datetime

def to_formatter(_type):
    origin = get_origin(_type)
    args = get_args(_type)

    # Base case: simple types
    if _type in (int, bool, str):
        return PrimitiveFormatter(_type)

    if _type is float:
        return FloatFormatter()

    if _type is list:
        return ListFormatter(DefaultFormatter())

    if _type is tuple:
        return TupleFormatter(DefaultFormatter())

    if _type is datetime:
        return DatetimeFormatter()
    # Enums
    if isinstance(_type, type) and issubclass(_type, Enum):
        return EnumFormatter(_type)

    # Dataclasses
    if isinstance(_type, type) and is_dataclass(_type):
        return DataClassFormatter(_type)

    NoneType = type(None)
    if origin is Union or origin is types.UnionType:
        non_none_args = [arg for arg in args if arg is not NoneType]
        if len(non_none_args) == 1:
            inner_formatter = to_formatter(non_none_args[0])
            inner_formatter.not_null = False
            return inner_formatter
        return DefaultFormatter()

    # list[X]
    if origin in (list, List):
        if len(args) == 1:
            return ListFormatter(to_formatter(args[0]))
        else:
            return ListFormatter(DefaultFormatter())

    # tuple[X, ...]
    if origin in (tuple, Tuple):
        if len(args) == 2 and args[1] is Ellipsis:
            return TupleFormatter(to_formatter(args[0]))
        else:
            return TupleFormatter(DefaultFormatter())

    # dict[str, X]
    if origin in (dict, Dict):
        if len(args) == 2:
            return DictFormatter(to_formatter(args[1]))
        return

    return DefaultFormatter()



class Format:
    @staticmethod
    def to_json(value, _type):
        return Format.get_formatter(_type).to_json(value, SerializationPath('/'))

    @staticmethod
    def from_json(value, _type):
        return Format.get_formatter(_type).from_json(value, SerializationPath('/'))

    @staticmethod
    def get_formatter(annotation) -> IFormatter:
        return to_formatter(annotation)
