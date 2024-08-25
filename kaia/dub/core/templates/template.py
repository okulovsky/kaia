from typing import *
from ..structures import IDubBinding, UnionDub, Dub, ToStrDub
from ..algorithms import ToStr, RegexpParser, Randomizer
from numpy.random import RandomState
from copy import copy, deepcopy
from uuid import uuid4
from .template_metadata import TemplateMetadata
from .paraphrase import Paraphrase
from .predefined_fields import PredefinedField



class ParserCache:
    _cache = {}

    @staticmethod
    def get(template: 'Template') -> RegexpParser:
        if template._uuid not in ParserCache._cache:
            parser = RegexpParser(template)
            ParserCache._cache[template._uuid] = parser
        return ParserCache._cache[template._uuid]





class Template:
    def __init__(self, *args: str, **kwargs: Union[Dub,IDubBinding]):
        args, kwargs = PredefinedField.fix_template_arguments(args, kwargs)
        self._init_fields(args, kwargs)
        if len(args) == 1 and len(kwargs) == 0 and not isinstance(args[0], str):
            if not isinstance(args[0], Dub):
                raise ValueError(f'First argument must be either str or Dub, but was {type(args[0])}')
            self.dub = args[0]
        else:
            sequences = UnionDub.create_sequences(args, kwargs)
            self.dub = UnionDub(sequences)

    def _init_fields(self, args, kwargs):
        self.name: Optional[str] = None
        self.value: Optional = None
        self.attached_dubs = kwargs
        self.string_templates = args
        self._meta = TemplateMetadata(self)
        self._uuid = uuid4()


    @staticmethod
    def free(s: str, **kwargs: Union[Dub,IDubBinding]):
        template = Template.__new__(Template)
        args, kwargs = PredefinedField.fix_template_arguments([s], kwargs)
        sequences = UnionDub.create_sequences(args, kwargs, auto_create_dub_factory=ToStrDub)
        template._init_fields(args, kwargs)
        template.dub = UnionDub(sequences)
        template.dub._strict_dict_equality_in_to_str = False
        return template



    def prepare(self):
        ParserCache.get(self)


    def with_name(self, name: str) -> 'Template':
        obj = self.clone()
        obj.name = name
        return obj

    @property
    def meta(self) -> TemplateMetadata['Template']:
        return self._meta


    def to_str(self, value):
        for result in ToStr(value).walk(self.dub):
            return result
        raise ValueError(f'Cannot transform {value} by dub {self.dub}')

    def to_all_strs(self, value):
        return tuple(ToStr(value).walk(self.dub))

    def parse(self, s):
        return ParserCache.get(self).parse(s)


    def get_random_value(self, random_state: Optional[RandomState] = None):
        if random_state is None:
            random_state = RandomState()
        randomizer = Randomizer(lambda z: z.get_random_value(random_state))
        options = randomizer.walk(self.dub).to_list()
        return random_state.choice(options)


    def utter(self, *args, **kwargs):
        from .utterance import Utterance
        if len(args)>1:
            raise ValueError('Only one unnamed argument is allowed')
        if len(args)==1:
            if isinstance(args[0], dict):
                return Utterance(self, args[0])
            elif len(self.attached_dubs) == 1:
                return Utterance(self, {list(self.attached_dubs)[0]:args[0]})
            else:
                raise ValueError('Unnamed argument must be dict, or value in case only one attached dub is known.')
        return Utterance(self, dict(**kwargs))

    def __call__(self, *args, **kwargs):
        return self.utter(*args, **kwargs)

    def substitute(self, dubs: Dict[str, Dub]) -> 'Template':
        new_dubs = copy(self.attached_dubs)
        for key, value in dubs.items():
            if key in new_dubs:
                new_dubs[key] = value
        template = Template(*self.string_templates, **new_dubs)
        template.name = self.name
        template._meta = copy(self._meta)
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


    def __contains__(self, item):
        from .utterance import Utterance
        if not isinstance(item, Utterance):
            raise ValueError(f'Only `Utterance` can be "in" template, but was {item}')
        return item.template == self

    def clone(self) -> 'Template':
        template = deepcopy(self)
        meta = template.meta.__dict__
        meta['_template'] = template
        template._meta = TemplateMetadata(**meta)
        return template

    @property
    def paraphrase(self) -> 'Paraphrase[Template]':
        return Paraphrase(self)


