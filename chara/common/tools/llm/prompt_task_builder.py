from typing import Callable, TypeVar, Generic
from brainbox import BrainBox
from brainbox.deciders import Ollama
from foundation_kaia.marshalling import Serializer
from foundation_kaia.prompters import Address, AddressLike
from .jinja_prompter import JinjaPrompter
from pathlib import Path
from copy import copy


T = TypeVar('T')

class PromptTaskBuilder(Generic[T]):
    def __init__(self,
                 model: str,
                 prompter: Path|str|Callable[[T], str]|None = None,
                 system_prompt: str|None = None,
                 debug: bool = False,
                 format_type: type|None = None,
                 options: Ollama.Options|None = None,
                 image_field: AddressLike|None = None
                 ):
        self.model = model
        self.system_prompt = system_prompt
        self.debug = debug
        self.format_type = format_type
        self._serializer = Serializer.parse(format_type) if format_type is not None else None
        self.prompter = None
        self.options = options
        self.image_field = image_field
        if prompter is not None:
            self.set_prompt(prompter)

    @property
    def json_schema(self) -> dict|None:
        if self._serializer is None:
            return None
        return self._serializer.to_json_schema().to_dict()

    def set_prompt(self, prompter: Path|str|Callable[[T], str], override: bool = False):
        if self.prompter is not None and not override:
            return
        if isinstance(prompter, str) or isinstance(prompter, Path):
            self.prompter = JinjaPrompter(prompter)
        else:
            self.prompter = prompter

    def _get_prompt(self, case) -> str:
        return self.prompter(case)

    def _get_options(self) -> Ollama.Options|None:
        if self._serializer is None:
            return self.options
        if self.options is not None:
            options = copy(self.options)
            options.format = self.json_schema
            return options
        return Ollama.Options(format=self.json_schema)

    def __call__(self, case) -> BrainBox.Task:
        prompt = self._get_prompt(case)
        if self.debug:
            print(prompt)
        image = None
        if self.image_field is not None:
            image = Address.parse(self.image_field).get(case)
        return Ollama.new_task(parameter=self.model).question(prompt, self.system_prompt, options=self._get_options(), image=image)
