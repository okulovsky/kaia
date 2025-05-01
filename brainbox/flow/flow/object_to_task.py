from typing import TypeVar, Generic, Any, Callable
from abc import ABC, abstractmethod
from ..prompters import IPrompter
from dataclasses import dataclass, field
import hashlib
from brainbox import BrainBoxTask

T = TypeVar("T")

class IObjectConverter(ABC, Generic[T]):
    @dataclass
    class Output:
        task: Any
        tags: dict = field(default_factory=dict)
        cache_key: str|None = None

    @abstractmethod
    def convert(self, object: T) -> 'IObjectConverter.Output':
        pass

class PromptBasedObjectConverter(IObjectConverter[T], Generic[T]):
    def __init__(self,
                 prompter: IPrompter[T],
                 model: str,
                 decider_name: str = 'Ollama',
                 decider_method: str = 'question',
                 prompt_argument_name: str = 'prompt'
                 ):
        self.prompter = prompter
        self.model = model
        self.decider_name = decider_name
        self.decider_method = decider_method
        self.prompt_argument_name = prompt_argument_name


    def convert(self, object) -> IObjectConverter.Output:
        prompt = self.prompter(object)
        task = BrainBoxTask(
            decider=self.decider_name,
            decider_method=self.decider_method,
            arguments={self.prompt_argument_name: prompt},
            decider_parameter=self.model,
        )
        tags = dict(prompt=prompt)
        key = self.model+'/'+prompt
        key = hashlib.blake2s(key.encode(), digest_size=16).hexdigest()
        return IObjectConverter.Output(
            task,
            tags,
            key,
        )

class FunctionalObjectToTask(IObjectConverter, Generic[T]):
    def __init__(self, function: Callable[[T], IObjectConverter.Output]):
        self.function = function

    def convert(self, object: T) -> 'IObjectConverter.Output':
        return self.function(object)


