from __future__ import annotations
from dataclasses import dataclass
from typing import Union, Type, Any, Generic, TypeVar, get_origin, get_args
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .annotation import Annotation



_T0 = TypeVar('_T0')
_T1 = TypeVar('_T1')
_T2 = TypeVar('_T2')
_T3 = TypeVar('_T3')
_T4 = TypeVar('_T4')
_SYNTHETIC_TYPEVARS = (_T0, _T1, _T2, _T3, _T4)


def _resolve_type(tp, type_args: dict):
    if isinstance(tp, TypeVar):
        return type_args.get(tp, object)
    origin = get_origin(tp)
    if origin is not None:
        args = get_args(tp)
        resolved = tuple(_resolve_type(a, type_args) for a in args)
        return origin[resolved[0]] if len(resolved) == 1 else origin[resolved]
    return tp

@dataclass
class GenericParameterDescription:
    generic_parameter: TypeVar
    generic_parameter_value: 'Annotation'

    @staticmethod
    def parse(typevar: TypeVar, type_args: dict) -> 'GenericParameterDescription':
        from .annotation import Annotation
        raw = type_args.get(typevar, object)
        ann = Annotation.parse(raw)
        return GenericParameterDescription(typevar, ann)

    def __eq__(self, other: 'GenericParameterDescription') -> bool:
        return (type(self) == type(other)
                and self.generic_parameter.__name__ == other.generic_parameter.__name__
                and self.generic_parameter_value == other.generic_parameter_value)

@dataclass
class DeclaredTypeMROElement:
    type: type
    generic_type: Union[Type, None]
    parameters: tuple[GenericParameterDescription,...]

    @property
    def type_map(self) -> dict[TypeVar, type] | None:
        if not self.parameters:
            return None
        return {
            p.generic_parameter: p.generic_parameter_value.raw_annotation
            for p in self.parameters
        }

    @staticmethod
    def parse(cls: type, type_args: dict) -> 'DeclaredTypeMROElement':
        class_params = getattr(cls, '__parameters__', ()) or tuple(type_args.keys())
        if not class_params:
            return DeclaredTypeMROElement(cls, None, ())
        param_descs = tuple(
            GenericParameterDescription.parse(p, type_args)
            for p in class_params
        )
        resolved = tuple(type_args.get(p, object) for p in class_params)
        generic_type = cls[resolved[0]] if len(resolved) == 1 else cls[resolved]
        return DeclaredTypeMROElement(cls, generic_type, param_descs)

class DeclaredTypeArgumentKind(Enum):
    type = 0
    generic_type = 1
    value = 2

@dataclass
class DeclaredType:
    kind: DeclaredTypeArgumentKind
    mro: tuple[DeclaredTypeMROElement,...]

    @property
    def self(self) -> DeclaredTypeMROElement:
        return self.mro[0]

    def find_type(self, t: Type) -> DeclaredTypeMROElement | None:
        for m in self.mro:
            if m.type is t:
                return m

    def create_instance(self, *args, **kwargs) -> Any:
        elem = self.mro[0]
        cls = elem.generic_type if elem.generic_type is not None else elem.type
        return cls(*args, **kwargs)


    @staticmethod
    def parse(value: Any, type_map: dict[TypeVar, type] | None = None) -> 'DeclaredType':
        origin = get_origin(value)

        if origin is not None:
            kind = DeclaredTypeArgumentKind.generic_type
            cls = origin
            cls_params = getattr(cls, '__parameters__', ())
            value_args = get_args(value)
            if not cls_params and value_args:
                cls_params = _SYNTHETIC_TYPEVARS[:len(value_args)]
            initial_args = {
                param: _resolve_type(arg, type_map) if type_map else arg
                for param, arg in zip(cls_params, value_args)
            }
        elif isinstance(value, type):
            kind = DeclaredTypeArgumentKind.type
            cls = value
            initial_args = {}
        else:
            kind = DeclaredTypeArgumentKind.value
            cls = type(value)
            if hasattr(value, '__orig_class__'):
                orig = value.__orig_class__
                initial_args = dict(zip(get_origin(orig).__parameters__, get_args(orig)))
            else:
                initial_args = {}

        filtered_mro = [c for c in cls.__mro__ if c is not Generic]

        # Build per-class type_args by propagating through __orig_bases__
        class_type_args = {}
        if initial_args:
            class_type_args[cls] = initial_args

        for c in filtered_mro:
            current_args = class_type_args.get(c, {})
            for base in getattr(c, '__orig_bases__', ()):
                base_origin = get_origin(base)
                if base_origin is None or base_origin is Generic:
                    continue
                base_params = getattr(base_origin, '__parameters__', ())
                if not base_params:
                    continue
                base_args = get_args(base)
                resolved = {
                    param: _resolve_type(arg, current_args)
                    for param, arg in zip(base_params, base_args)
                }
                class_type_args.setdefault(base_origin, resolved)

        descriptions = tuple(
            DeclaredTypeMROElement.parse(c, class_type_args.get(c, {}))
            for c in filtered_mro
        )
        return DeclaredType(kind, descriptions)
