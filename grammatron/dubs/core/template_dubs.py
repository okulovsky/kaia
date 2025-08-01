from .template_dub_base import TemplateDub
from .sequence_dub import SequenceDub
from typing import *

class DataclassTemplateDub(TemplateDub):
    def __init__(self, _type: Type, *definitions: str):
        self._type = _type
        super().__init__(*definitions)

    def value_to_variables(self, value: Any):
        if not isinstance(value, self._type):
            raise ValueError(f"Expected instance of {self._type}, but was {value}")
        return {k:v for k,v in value.__dict__.items() if v is not None}

    def variables_to_value(self, variables: dict[str, Any]) -> Any:
        return self._type(**variables)


class DictTemplateDub(TemplateDub):
    def __init__(self, *definitions: str|SequenceDub):
        super().__init__(*definitions)

    def value_to_variables(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError(f"Expected dict, but was {value}")
        return value

    def variables_to_value(self, variables: dict[str, Any]) -> Any:
        return variables


class FunctionalTemplateDub(TemplateDub):
    def __init__(self,
                 definitions: Iterable[Union[str, TemplateDub]],
                 value_to_variables: Callable[[Any], dict],
                 variables_to_value: Callable[[dict], Any]
                 ):
        self._value_to_variables = value_to_variables
        self._variables_to_value = variables_to_value
        if isinstance(definitions, str):
            raise ValueError("definitions should be a Iterable of str, not a str")
        super().__init__(*definitions)

    def variables_to_value(self, variables: dict[str, Any]) -> Any:
        return self._variables_to_value(variables)

    def value_to_variables(self, value: Any) ->dict[str,Any]:
        return self._value_to_variables(value)

