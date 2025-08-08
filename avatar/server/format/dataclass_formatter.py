from typing import get_type_hints, Type
from .formatter import IFormatter, SerializationPath
from dataclasses import is_dataclass
import sys
import builtins


class DataClassFormatter(IFormatter):
    def __init__(self, _type):
        if not is_dataclass(_type):
            raise ValueError(f"Must be created for dataclass type, not {_type}")

        self._type = _type
        self._formatters = None

    @staticmethod
    def get_type_hints(_type):
        module = sys.modules[_type.__module__]
        globalns = module.__dict__.copy()
        globalns.update(vars(builtins))
        globalns[_type.__name__] = _type

        hints = get_type_hints(_type, globalns=globalns)
        return hints

    def _get_formatters(self) -> dict[str, IFormatter]:
        if self._formatters is None:
            hints = DataClassFormatter.get_type_hints(self._type)
            from .format import Format
            self._formatters = {name: Format.get_formatter(_type) for name, _type in hints.items()}
        return self._formatters

    def _to_json(self, value, path: SerializationPath):
        path.to_json.check_type(value, self._type)
        return {
            name: formatter.to_json(getattr(value, name), path.append(name))
            for name, formatter in self._get_formatters().items()
        }

    def _from_json(self, value, path: SerializationPath):
        path.from_json.check_type(value, dict)
        instance = object.__new__(self._type)
        for name, formatter in self._get_formatters().items():
            setattr(
                instance,
                name,
                formatter.from_json(value.get(name, None), path.append(name))
            )
        return instance




