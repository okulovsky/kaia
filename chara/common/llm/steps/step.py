from typing import Any, Callable
from brainbox.deciders import Ollama
from foundation_kaia.prompters import AddressLike


class LLMRequestStep:
    def fill_template_entities(self, case: Any, template_entities: dict):
        pass

    def set_entity(self, template_entities: dict, key: str, value: Any):
        """Contributes an entity that only one step may own."""
        if key in template_entities:
            raise ValueError(
                f"{type(self).__name__} cannot set the template entity `{key}`: it is already set. "
                f"Steps that describe the expected answer, such as Questionnaire and "
                f"ResultTypization, are not meant to be combined in one request."
            )
        template_entities[key] = value

    def fill_arguments(self, case: Any, template_entities: dict, arguments: dict):
        pass

    def update_options(self, case: Any, options: Ollama.Options|None) -> Ollama.Options|None:
        return options

    def get_divider(self) -> Callable[[str], list]|None:
        return None

    def get_parser(self) -> Callable[[Any, str], Any]|None:
        return None

    def get_assignment_address(self) -> AddressLike|None:
        return None
