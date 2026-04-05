import collections.abc
import types
from typing import Callable, get_args
from dataclasses import dataclass
from .binding_settings import BindingSettings, EndpointBindingSettings
from .rule import Rule, RuleConnector, SyncCallSpec
from foundation_kaia.marshalling_2.reflector.signature import Signature, FunctionKind
from foundation_kaia.marshalling_2.reflector.declared_type import DeclaredType


def _get_input_type(sig: Signature) -> type | None:
    args = sig.proper_arguments
    if len(args) != 1:
        raise ValueError(f"'{sig.name}': message handler must have exactly one argument (excluding self), got {len(args)}")
    ann = args[0].annotation
    if ann.not_annotated:
        return None
    return ann.types[0].mro[0].type


def _unroll(dt: DeclaredType) -> list[type]:
    t = dt.mro[0].type
    if t is type(None):
        return []
    if t in (tuple, collections.abc.Iterable):
        generic = dt.mro[0].generic_type
        return [a for arg in get_args(generic) if arg is not ... for a in _unroll_raw(arg)]
    return [t]


def _unroll_raw(tp) -> list[type]:
    from foundation_kaia.marshalling_2.reflector.annotation import Annotation
    ann = Annotation.parse(tp)
    result = []
    for dt in ann.types:
        result.extend(_unroll(dt))
    return result


def _get_output_types(sig: Signature) -> tuple[type, ...] | None:
    ann = sig.returned_type
    if ann.not_annotated:
        return None
    result = []
    for dt in ann.types:
        result.extend(_unroll(dt))
    return tuple(result) if result else None


@dataclass
class MessageHandlerAttributes:
    calls: tuple[SyncCallSpec, ...]


@dataclass
class RuleCreator:
    method: Callable
    settings: BindingSettings
    attributes: MessageHandlerAttributes | None

    def _signature(self) -> Signature:
        func = self.method.__func__ if isinstance(self.method, types.MethodType) else self.method
        return Signature.parse(func)

    def get_host(self):
        if isinstance(self.method, types.MethodType):
            return self.method.__self__
        return None

    def get_name(self):
        if self.get_host() is None:
            if self.settings.custom_name is not None:
                return self.settings.custom_name
            else:
                return self.method.__name__
        else:
            if self.settings.custom_name is not None:
                return self.settings.custom_name + '/' + self.method.__name__
            else:
                return type(self.get_host()).__name__ + '/' + self.method.__name__

    def get_connector(self):
        sig = self._signature()
        input_type = _get_input_type(sig)
        setting = self.settings.get_setting_for_method(self.method)
        if setting is None:
            setting = self.settings.get_setting_for_type(input_type)
        if setting is None:
            include = exclude = None
        else:
            include = EndpointBindingSettings.normalize(setting.include_senders)
            exclude = EndpointBindingSettings.normalize(setting.exclude_senders)
        return RuleConnector(input_type, include, exclude)

    def get_rule(self):
        if self.attributes is None:
            self.attributes = MessageHandlerAttributes(())
        sig = self._signature()
        return Rule(
            self.get_name(),
            self.get_connector(),
            self.get_host(),
            self.method,
            self.settings.is_asynchronous,
            _get_output_types(sig),
            self.attributes.calls,
        )
