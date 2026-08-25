import json
from typing import Any

from brainbox.deciders import Ollama
from foundation_kaia.marshalling import Serializer

from .step import LLMRequestStep
from .questions import Json


class ResultTypization(LLMRequestStep):
    """Constrains the answer to the JSON schema of `result_type` and deserializes it back.

    `example` is an instance of `result_type` shown to the model as the `example`
    template entity; a schema is not a substitute, so without one there is no entity.
    """

    def __init__(self, result_type: type, example: Any = None):
        self.result_type = result_type
        self.example = example
        self.serializer = Serializer.parse(result_type)
        self.is_array = Json.is_array(self.serializer)
        self.schema = self.serializer.to_json_schema().to_dict()

    def fill_template_entities(self, case: Any, template_entities: dict):
        if self.example is not None:
            self.set_entity(template_entities, 'example', json.dumps(self.serializer.to_json(self.example), indent=2))

    def update_options(self, case: Any, options: Ollama.Options|None) -> Ollama.Options|None:
        if options is not None and options.format is not None:
            raise ValueError(
                "ResultTypization cannot set the answer format because it is already set. "
                "ResultTypization and Questionnaire both describe the expected answer and "
                "are not meant to be combined in one request."
            )
        return options + Ollama.Options(format=self.schema)

    def get_parser(self):
        def parse(case: Any, output: str) -> Any:
            value = Json.parse_array(output) if self.is_array else Json.parse_object(output)
            try:
                return self.serializer.from_json(value)
            except Exception as e:
                raise Exception(f"Exception when parsing this JSON\n{value}\nfrom text\n{output}") from e
        return parse
