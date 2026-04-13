from typing import Any, TypeVar
from .type_handler import ITypeHandler, SerializationContext
from ..json_schema import JsonSchema


def _is_json(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float, str)):
        return True
    if isinstance(value, list):
        return all(_is_json(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _is_json(v) for k, v in value.items())
    return False


class JSONHandler(ITypeHandler):
    """Handler for the JSON type alias (dict|list|str|float|int|None).

    Accepts any JSON-compatible value in to_json (raises TypeError otherwise)
    and passes from_json values through as-is (they are already JSON by definition).
    """

    @property
    def python_type(self) -> type:
        return object

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not _is_json(value):
            raise TypeError(
                f"Expected JSON-compatible value at {context.current_path}, got {type(value)}"
            )
        return value

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        return json_value

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {}
