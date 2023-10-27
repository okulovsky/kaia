from typing import *
from ..structures import DubBinding, UnionDub, Dub
from ..algorithms import ToStr, Parser, Randomizer
from numpy.random import RandomState
from copy import copy
from .utterance_assertion import UtteranceAssertion

class Template:
    def __init__(self, *args: str, **kwargs: Union[Dub,DubBinding]):
        self.name = None
        self.value = None
        if len(args) == 1 and len(kwargs) == 0 and not isinstance(args[0], str):
            if not isinstance(args[0], Dub):
                raise ValueError(f'First argument must be either str or Dub, but was {type(args[0])}')
            self.dub = args[0]
        else:
            sequences = UnionDub.create_sequences(args, kwargs)
            self.dub = UnionDub(sequences)

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

    def get_placeholder_value(self):
        randomizer = Randomizer(lambda z: z.get_placeholder_value())
        return randomizer.walk(self.dub).first()

    def utter(self, *args, **kwargs):
        if len(args)>1:
            raise ValueError('Only one unnamed argument is allowed')
        if len(args)==1:
            return Utterance(self, args[0])
        return Utterance(self, dict(**kwargs))



class Utterance:
    def __init__(self, template: Template, value: Any):
        self.template = template
        self.value = value

    def to_str(self):
        return self.template.to_str(self.value)

    @property
    def assertion(self) -> UtteranceAssertion:
        return UtteranceAssertion(self)


