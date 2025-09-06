from typing import *
from ..dubs import RegexParser, VariableAssignment, IDub

from copy import copy, deepcopy
from foundation_kaia.prompters import Prompter
from dataclasses import dataclass

@dataclass
class TemplateContext:
    context: Prompter|None = None
    reply_to: Tuple['TemplateBase',...] = None
    reply_details: Prompter|None = None

TDub = TypeVar('TDub', bound=IDub)
TSelf = TypeVar('TSelf', bound='TemplateBase')

class TemplateBase(Generic[TDub]):
    def __init__(self, dub: TDub, _type: Type|None = None):
        self._dub = dub
        self._name: Optional[str] = None
        self._context: TemplateContext = TemplateContext()
        self._paraphrasing_allowed: bool|None = None
        self._type = _type
        self._custom_name: bool = False

    def clone(self: TSelf) -> TSelf:
        template = deepcopy(self)
        return template

    def with_name(self: TSelf, name: str) -> TSelf:
        obj = self.clone()
        obj._name = name
        obj._custom_name = True
        return obj

    @property
    def dub(self) -> TDub:
        return self._dub

    def get_name(self) -> str|None:
        return self._name

    def get_type(self) -> type|None:
        return self._type

    def context(self,
                context: str|None = None,
                reply_to: Union['TemplateBase', Iterable['TemplateBase'], None] = None,
                reply_details: str|None = None
                ) -> TSelf:
        obj = self.clone()
        if isinstance(context, str):
            context = Prompter(context)
        if isinstance(reply_details, str):
            reply_details = Prompter(reply_details)
        if isinstance(reply_to, TemplateBase):
            reply_to = (reply_to,)
        if reply_to is not None:
            reply_to = tuple(reply_to)
        obj._context = TemplateContext(context, reply_to, reply_details)
        return obj

    def get_context(self) -> TemplateContext:
        return self._context

    def paraphrasing(self, paraphrasing_allowed = True):
        obj = self.clone()
        obj._paraphrasing_allowed = paraphrasing_allowed
        return obj

    def no_paraphrasing(self):
        obj = self.clone()
        obj._paraphrasing_allowed = False
        return obj

    def to_str(self, value) -> str:
        return self.utter(value).to_str()

    def _get_single_attached_subdub_name(self) -> str|None:
        return None

    def utter(self, *args, **kwargs):
        from .utterance import Utterance

        resulting_kwargs = {}
        for arg in args:
            if isinstance(arg, VariableAssignment):
                if arg.value is not None:
                    resulting_kwargs[arg.variable.name] = arg.value
            elif len(args) > 1:
                raise ValueError("If more than one arg is present, they all must be VariableAssignment")
            else:
                if self._type is not None:
                    if isinstance(arg, self._type):
                        return Utterance(self, arg)
                    else:
                        raise ValueError(f"This is typed template with type {self._type}. Argument of this type was expected, but was {arg}")
                else:
                    if isinstance(arg, dict):
                        resulting_kwargs = arg
                    elif self._get_single_attached_subdub_name() is not None:
                        resulting_kwargs[self._get_single_attached_subdub_name()] = arg
                    else:
                        raise ValueError("More than one `dub` is present, unclear of where to attach")
        for key, value in kwargs.items():
            resulting_kwargs[key] = value

        return Utterance(self, resulting_kwargs)

    def __call__(self, *args, **kwargs):
        return self.utter(*args, **kwargs)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, TemplateBase):
            return False
        if self._custom_name and other._custom_name and self.get_name() == other.get_name():
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __contains__(self, item):
        from .utterance import Utterance
        if not isinstance(item, Utterance):
            #raise ValueError(f'Only `Utterance` can be "in" template, but was {item}')
            return False
        return item.template == self


