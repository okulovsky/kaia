from dataclasses import dataclass
from enum import IntEnum
from inspect import Parameter
from typing import Any, Callable, TypeVar, get_type_hints
from .annotation import Annotation
import inspect


class ArgumentKind(IntEnum):
    POSITIONAL_ONLY = Parameter.POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD = Parameter.POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL = Parameter.VAR_POSITIONAL
    KEYWORD_ONLY = Parameter.KEYWORD_ONLY
    VAR_KEYWORD = Parameter.VAR_KEYWORD

class FunctionKind(IntEnum):
    FUNCTION = 0
    LAMBDA = 1
    INSTANCE_METHOD = 2
    CLASS_METHOD = 3
    STATIC_METHOD = 4


_NO_DEFAULT = Parameter.empty

@dataclass
class FunctionArgumentDescription:
    name: str | None
    index: int | None
    annotation: Annotation
    kind: ArgumentKind
    default: Any = _NO_DEFAULT

    @property
    def has_default(self) -> bool:
        return self.default is not _NO_DEFAULT


@dataclass
class Signature:
    name: str | None
    callable: Callable
    kind: FunctionKind
    arguments: tuple[FunctionArgumentDescription, ...]
    returned_type: Annotation


    @property
    def proper_arguments(self) -> tuple['FunctionArgumentDescription', ...]:
        if self.kind == FunctionKind.INSTANCE_METHOD and self.arguments:
            return self.arguments[1:]
        return self.arguments

    def assign_parameters_to_names(self, *args, **kwargs) -> dict[str, Any]:
        arguments = self.arguments
        if self.kind == FunctionKind.INSTANCE_METHOD and arguments:
            arguments = arguments[1:]

        for a in arguments:
            if a.kind == ArgumentKind.POSITIONAL_ONLY:
                raise TypeError(
                    f"'{self.name}()' has positional-only parameter '{a.name}' "
                    f"that cannot be assigned to a name"
                )
            if a.kind == ArgumentKind.VAR_POSITIONAL:
                raise TypeError(
                    f"'{self.name}()' has *{a.name} parameter "
                    f"that cannot be assigned to a name"
                )
            if a.kind == ArgumentKind.VAR_KEYWORD:
                raise TypeError(
                    f"'{self.name}()' has **{a.name} parameter "
                    f"that cannot be assigned to a name"
                )

        positional_params = [a for a in arguments if a.kind == ArgumentKind.POSITIONAL_OR_KEYWORD]
        all_named = {a.name for a in positional_params} | {a.name for a in arguments if a.kind == ArgumentKind.KEYWORD_ONLY}

        result: dict[str, Any] = {}

        if len(args) > len(positional_params):
            raise TypeError(
                f"'{self.name}()' takes {len(positional_params)} positional arguments "
                f"but {len(args)} were given"
            )

        for i, value in enumerate(args):
            result[positional_params[i].name] = value

        for key, value in kwargs.items():
            if key in result:
                raise TypeError(
                    f"'{self.name}()' got multiple values for argument '{key}'"
                )
            if key in all_named:
                result[key] = value
            else:
                raise TypeError(
                    f"'{self.name}()' got an unexpected keyword argument '{key}'"
                )

        missing = [a.name for a in arguments if not a.has_default and a.name not in result]
        if missing:
            names = ', '.join(repr(n) for n in missing)
            raise TypeError(
                f"'{self.name}()' missing required arguments: {names}"
            )

        return result

    @staticmethod
    def parse(cl: Callable, owner: type | None = None, type_map: dict[TypeVar, type] | None = None) -> 'Signature':
        sig = inspect.signature(cl)
        _cl_for_hints = cl
        while hasattr(_cl_for_hints, '__wrapped__'):
            _cl_for_hints = _cl_for_hints.__wrapped__
        hints = get_type_hints(_cl_for_hints)

        arguments = []
        positional_index = 0
        for param_name, param in sig.parameters.items():
            if param_name in hints:
                annotation = Annotation.parse(hints[param_name], type_map)
            else:
                annotation = Annotation.default()

            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                index = positional_index
                positional_index += 1
            elif param.kind == param.VAR_POSITIONAL:
                index = positional_index
                # don't increment — var-positional consumes the rest
            else:
                index = None

            arguments.append(FunctionArgumentDescription(
                name=param_name,
                index=index,
                annotation=annotation,
                kind=ArgumentKind(param.kind),
                default=param.default,
            ))

        if 'return' in hints:
            returned_types = Annotation.parse(hints['return'], type_map)
        else:
            returned_types = Annotation.default()

        name = getattr(cl, '__name__', None)
        kind = _detect_kind(cl, name, owner)

        return Signature(
            name=name,
            callable=cl,
            kind=kind,
            arguments=tuple(arguments),
            returned_type=returned_types,
        )


def _detect_kind(cl: Callable, name: str | None, owner: type | None) -> FunctionKind:
    if name == '<lambda>':
        return FunctionKind.LAMBDA
    if inspect.ismethod(cl) and isinstance(cl.__self__, type):
        return FunctionKind.CLASS_METHOD
    if _detect_static(cl, owner):
        return FunctionKind.STATIC_METHOD
    if _is_defined_in_class(cl):
        return FunctionKind.INSTANCE_METHOD
    return FunctionKind.FUNCTION


def _detect_static(cl: Callable, owner: type | None) -> bool:
    if inspect.ismethod(cl):
        return False
    func_name = getattr(cl, '__name__', None)
    # If the owner class is provided, check its dict directly
    if owner is not None and func_name is not None:
        return isinstance(owner.__dict__.get(func_name), staticmethod)
    # Fallback: try to find the owner via qualname + module traversal
    qualname = getattr(cl, '__qualname__', '')
    if '.' not in qualname or '<' in qualname:
        return False
    class_path, method_name = qualname.rsplit('.', 1)
    module = inspect.getmodule(cl)
    if module is None:
        return False
    resolved = module
    for part in class_path.split('.'):
        resolved = getattr(resolved, part, None)
        if resolved is None:
            return False
    return isinstance(resolved.__dict__.get(method_name), staticmethod)


def _is_defined_in_class(cl: Callable) -> bool:
    if inspect.ismethod(cl):
        return True
    qualname = getattr(cl, '__qualname__', '')
    if '.' not in qualname:
        return False
    # The immediate parent in the qualname must be a class name, not <locals>
    parent = qualname.rsplit('.', 1)[0]
    return not parent.endswith('>')