import base64
import importlib
import pickle
from typing import Any
from .handlers.type_handler import SerializationContext
from ..reflector.annotation import Annotation


class TypeTools:
    @staticmethod
    def type_to_full_name(tp: type) -> str:
        return f"{tp.__module__}.{tp.__qualname__}"

    @staticmethod
    def full_name_to_type(full_name: str) -> type:
        parts = full_name.split('.')
        for i in range(len(parts) - 1, 0, -1):
            module_name = '.'.join(parts[:i])
            try:
                module = importlib.import_module(module_name)
                obj = module
                for attr in parts[i:]:
                    obj = getattr(obj, attr)
                if isinstance(obj, type):
                    return obj
            except (ImportError, AttributeError):
                continue
        raise TypeError(f"Cannot resolve type: {full_name}")

    @staticmethod
    def value_to_base64_pickle(value: Any) -> str:
        return base64.b64encode(pickle.dumps(value)).decode('ascii')

    @staticmethod
    def base64_pickle_to_value(data: str) -> Any:
        return pickle.loads(base64.b64decode(data))

    @staticmethod
    def serialize(value: Any, tp: Any = None, allow_base64: bool = True) -> Any:
        from .serializer import Serializer
        ctx = SerializationContext(path=[], allow_base64=allow_base64)
        annotation = Annotation.parse(tp if tp is not None else type(value))
        return Serializer(annotation).to_json(value, ctx)

    @staticmethod
    def deserialize(json_value: Any, tp: type, allow_base64: bool = True) -> Any:
        from .serializer import Serializer
        ctx = SerializationContext(path=[], allow_base64=allow_base64)
        annotation = Annotation.parse(tp)
        return Serializer(annotation).from_json(json_value, ctx)
