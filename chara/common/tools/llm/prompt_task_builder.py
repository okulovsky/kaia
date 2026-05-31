from dataclasses import dataclass
from typing import Callable, Any, TypeVar, Generic
from brainbox import BrainBox
from brainbox.deciders import Ollama
from foundation_kaia.prompters import JinjaPrompter
from pathlib import Path
from abc import ABC, abstractmethod

T = TypeVar('T')

class PromptTaskBuilder(Generic[T]):
    def __init__(self,
                 model: str,
                 prompter: Callable[[T], str]|None = None,
                 *,
                 prompt_file: Path|None = None,
                 system_prompt: str|None = None,
                 case_to_key: Callable[[T], str|None]|None = None,
                 debug: bool = False
                 ):
        self.model = model
        self.key_to_prompter: dict[str|None, Callable[[T], str]]|None = None
        self.system_prompt = system_prompt
        self.case_to_key = case_to_key
        self.debug = debug
        if prompter is not None:
            self.key_to_prompter = { None: prompter }
            if prompt_file is not None:
                raise ValueError("Cannot specify both `prompter` and `prompt_file`")
        if prompt_file is not None:
            self.read_prompt(prompt_file)

    @property
    def main_prompter(self) -> Callable[[T], str]|None:
        if self.key_to_prompter is None:
            return None
        return self.key_to_prompter.get(None, None)

    @main_prompter.setter
    def main_prompter(self, value: Callable[[T], str]|None):
        if self.key_to_prompter is None:
            self.key_to_prompter = {}
        self.key_to_prompter[None] = value

    def read_prompt(self, content: Path|str):
        if isinstance(content, Path):
            text = content.read_text()
        else:
            text = content
        key_to_prompt = {}
        current_key = None
        for line in text.splitlines(keepends=True):
            if line.startswith('# KEY '):
                current_key = line[len('# KEY '):].strip()
                continue
            if current_key not in key_to_prompt:
                key_to_prompt[current_key] = ''
            key_to_prompt[current_key] += line
        self.key_to_prompter = {key: JinjaPrompter(value) for key, value in key_to_prompt.items()}

    def read_default_prompt(self, path: Path):
        if self.key_to_prompter is None:
            self.read_prompt(path)

    def _get_prompter(self, case: T) -> Callable[[T], str]:
        if self.key_to_prompter is None:
            raise ValueError("Not initialized")
        if len(self.key_to_prompter) == 0:
            raise ValueError("Erroneously initialized, but there are no prompts")
        if self.case_to_key is None:
            if len(self.key_to_prompter) > 1:
                raise ValueError("case_to_key is not set, but there are key-based options")
            if self.main_prompter is None:
                raise ValueError("case_to_key is not set, there is one prompt, but it's key-based, not default")
            return self.main_prompter
        key = self.case_to_key(case)
        if key is None:
            if self.main_prompter is None:
                raise ValueError("Default key is requested, but the main_prompter is not set")
            return self.main_prompter
        if key in self.key_to_prompter:
            return self.key_to_prompter.get(key)
        if self.main_prompter is None:
            raise ValueError(f"Key {key} is requested, it is missing and the main prompter is not set")
        return self.main_prompter

    def _get_prompt(self, case: T) -> str:
        prompter = self._get_prompter(case)
        prompt = prompter(case)
        return prompt

    def __call__(self, case) -> BrainBox.Task:
        prompt = self._get_prompt(case)
        if self.debug:
            print(prompt)
        return Ollama.new_task(parameter=self.model).question(prompt, self.system_prompt)
