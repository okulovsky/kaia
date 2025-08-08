from .default_formatter import IFormatter, SerializationPath
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class ListFormatter(IFormatter):
    element_formatter: IFormatter

    def _to_json(self, value, path: SerializationPath):
        path.to_json.check_type(value, list)
        return [self.element_formatter.to_json(v, path.append(i)) for i, v in enumerate(value)]

    def _from_json(self, value, path: SerializationPath):
        path.from_json.check_type(value, list)
        return [self.element_formatter.from_json(v, path.append(i)) for i, v in enumerate(value)]


@dataclass
class TupleFormatter(IFormatter):
    element_formatter: IFormatter

    def _to_json(self, value, path: SerializationPath):
        path.to_json.check_type(value, tuple)
        return [self.element_formatter.to_json(v, path.append(i)) for i, v in enumerate(value)]

    def _from_json(self, value, path: SerializationPath):
        path.from_json.check_type(value, list)
        return tuple(self.element_formatter.from_json(v, path.append(i)) for i, v in enumerate(value))


@dataclass
class PrimitiveFormatter(IFormatter):
    _type: type

    def _to_json(self, value, path: SerializationPath):
        path.to_json.check_type(value, self._type)
        return value

    def _from_json(self, value, path: SerializationPath):
        path.from_json.check_type(value, self._type)
        return value

class FloatFormatter(IFormatter):
    def _to_json(self, value, path: SerializationPath):
        path.to_json.check_type(value, (int, float))
        return value

    def _from_json(self, value, path: SerializationPath):
        path.from_json.check_type(value, (int, float))
        return value




@dataclass
class DictFormatter(IFormatter):
    element_formatter: IFormatter

    def _to_json(self, value, path: SerializationPath):
        path.to_json.check_type(value, dict)
        return {k: self.element_formatter.to_json(v, path.append(k)) for k, v in value.items()}

    def _from_json(self, value, path: SerializationPath):
        path.from_json.check_type(value, dict)
        return {k: self.element_formatter.from_json(v, path.append(k)) for k, v in value.items()}


class DatetimeFormatter(IFormatter):
    def _to_json(self, value, path: SerializationPath):
        path.to_json.check_type(value, datetime)
        return datetime.isoformat(value)

    def _from_json(self, value, path: SerializationPath):
        path.from_json.check_type(value, str)
        return datetime.fromisoformat(value)


@dataclass
class EnumFormatter(IFormatter):
    _type: type[Enum]

    def _to_json(self, value, path: SerializationPath):
        path.to_json.check_type(value, self._type)
        return value.name

    def _from_json(self, value, path: SerializationPath):
        path.from_json.check_type(value, str)
        if value not in self._type.__members__:
            path.from_json.exc(f'{self._type} is expected, but the values was {value}')
        return self._type[value]








