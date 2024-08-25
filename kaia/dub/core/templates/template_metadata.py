from typing import *
from dataclasses import dataclass
from enum import Enum
from copy import copy


T = TypeVar("T")

@dataclass(frozen=True)
class ParaphraseInfo:
    class Type(Enum):
        Instead = 0
        After = 1

    type: 'ParaphraseInfo.Type'
    description: None|str
    as_story: bool


@dataclass(frozen=True)
class TemplateMetadata(Generic[T]):
    _template: T
    reply_to: Optional[T] = None
    paraphrase: None|ParaphraseInfo = None
    input_description: None|str = None

    def set(self,
               reply_to: Optional[T] = None,
               paraphrase: None|dict = None,
               input_description: None|str = None,
               ) -> T:
        args = copy(self.__dict__)
        if reply_to is not None:
            args['reply_to'] = reply_to
        if paraphrase is not None:
            args['paraphrase'] = paraphrase
        if input_description is not None:
            args['input_description'] = input_description
        new_template = self._template.clone()
        new_template._meta = TemplateMetadata(**args)
        return new_template








