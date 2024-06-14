from typing import *
from ..structures import DubBinding, UnionDub, Dub
from ..algorithms import ToStr, Parser, Randomizer
from numpy.random import RandomState
from copy import copy
from .utterance_assertion import UtteranceAssertion

class Template:
    def __init__(self, *args: str, **kwargs: Union[Dub,DubBinding]):
        self.name: Optional[str] = None
        self.value: Optional = None
        self.reply_to: Optional[Template] = None
        self.attached_dubs = kwargs
        self.string_templates = args
        if len(args) == 1 and len(kwargs) == 0 and not isinstance(args[0], str):
            if not isinstance(args[0], Dub):
                raise ValueError(f'First argument must be either str or Dub, but was {type(args[0])}')
            self.dub = args[0]
        else:
            sequences = UnionDub.create_sequences(args, kwargs)
            self.dub = UnionDub(sequences)

    def as_reply_to(self, template: 'Template') -> 'Template':
        obj = copy(self)
        obj.reply_to = template
        return obj

    def with_name(self, name: str) -> 'Template':
        obj = copy(self)
        obj.name = name
        return obj



    def to_str(self, value):
        for result in ToStr(value).walk(self.dub):
            return result
        raise ValueError(f'Cannot transform {value} by dub {self.dub}')

    def to_all_strs(self, value):
        return tuple(ToStr(value).walk(self.dub))

    def parse(self, s):
        result = list(Parser(s).walk(self.dub))
        if len(result) == 0:
            raise ValueError(f'Cannot parse string\n{s}\n in template {self.dub.get_name()}')
        if len(result) > 1:
            raise ValueError(f'Ambiguous parsing')
        return result[0]

    def get_random_value(self, random_state: Optional[RandomState] = None):
        if random_state is None:
            random_state = RandomState()
        randomizer = Randomizer(lambda z: z.get_random_value(random_state))
        options = randomizer.walk(self.dub).to_list()
        return random_state.choice(options)


    def utter(self, *args, **kwargs):
        if len(args)>1:
            raise ValueError('Only one unnamed argument is allowed')
        if len(args)==1:
            return Utterance(self, args[0])
        return Utterance(self, dict(**kwargs))

    def substitute(self, dubs: Dict[str, Dub]) -> 'Template':
        new_dubs = copy(self.attached_dubs)
        for key, value in dubs.items():
            if key in new_dubs:
                new_dubs[key] = value
        template = Template(*self.string_templates, **new_dubs)
        template.name = self.name
        template.reply_to = self.reply_to
        return template

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Template):
            return False
        if self.name is not None and other.name is not None and self.name == other.name:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)




class Utterance:
    def __init__(self, template: Template, value: Any):
        self.template = template
        self.value = value

    def to_str(self):
        return self.template.to_str(self.value)

    @property
    def assertion(self) -> UtteranceAssertion:
        return UtteranceAssertion(self)

    def __str__(self):
        return '[Utterance] '+self.to_str()


