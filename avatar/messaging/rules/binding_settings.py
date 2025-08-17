from dataclasses import dataclass, field
from typing import Callable
import inspect

def _base_func(x):
    return inspect.unwrap(getattr(x, "__func__", x))


@dataclass
class EndpointBindingSettings:
    message_type: type|None = None
    method: Callable|None = None
    include_senders: tuple[str|type,...]|None = None
    exclude_senders: tuple[str|type,...]|None = None

    @staticmethod
    def normalize(arg: tuple[str|type,...]|None) -> tuple[str,...]|None:
        if arg is None:
            return arg
        return tuple(z.__name__ if isinstance(z, type) else z for z in arg)





@dataclass
class TypeBindingSettingsBuilder:
    _settings: 'BindingSettings'
    _addition: EndpointBindingSettings

    def _add(self):
        self._settings.endpoint_settings.append(self._addition)
        return self._settings

    def to(self, *types: type|str) -> 'BindingSettings':
        self._addition.include_senders = types
        return self._add()

    def to_all_except(self, *types: type|str) -> 'BindingSettings':
        self._addition.exclude_senders = types
        return self._add()

@dataclass
class BindingSettings:
    is_asynchronous: bool = False
    endpoint_settings: list[EndpointBindingSettings] = field(default_factory=list)
    custom_name: str|None = None

    def with_name(self, name: str) -> 'BindingSettings':
        self.custom_name = name
        return self

    def asynchronous(self, is_asynchronous: bool = True) -> 'BindingSettings':
        self.is_asynchronous = is_asynchronous
        return self

    def bind_type(self, message_type: type) -> TypeBindingSettingsBuilder:
        return TypeBindingSettingsBuilder(self, EndpointBindingSettings(message_type=message_type))

    def bind_method(self, method: Callable):
        return TypeBindingSettingsBuilder(self, EndpointBindingSettings(method=method))

    def get_setting_for_method(self, method: Callable) -> EndpointBindingSettings|None:
        result = []
        for e in self.endpoint_settings:
            if _base_func(e.method) is _base_func(method):
                result.append(e)
        if len(result) > 1:
            raise ValueError("Only one rule for each method is allowed")
        elif len(result) == 0:
            return None
        return result[0]

    def get_setting_for_type(self, message_type: type) -> EndpointBindingSettings|None:
        result = [e for e in self.endpoint_settings if e.message_type is message_type]
        if len(result) > 1:
            raise ValueError("Only one rule for each message_type is allowed")
        elif len(result) == 0:
            return None
        return result[0]


