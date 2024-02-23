from .walker_state import *
from ..structures import ConstantDub, SetDub
from dataclasses import dataclass
from ..utils import rhasspy_nlu

@dataclass
class Content:
    constant: Optional[str] = None
    variable: Optional[str] = None
    alternatives: Optional[List[str]] = None

@dataclass
class IniRuleRecord:
    headers: Dict[str, Iterable[str]]
    content: List[Content]
    var_code: Tuple[str,...]

    def content_to_ini(self):
        result = []
        for c in self.content:
            if c.constant is not None:
                v = rhasspy_nlu.escape_for_rhasspy(c.constant)
                result.append(v)
            elif c.variable is not None:
                result.append(f'<{c.variable}>{{{c.variable}}}')
            elif c.alternatives is not None:
                result.append('('+'|'.join(c.alternatives)+')')
            else:
                raise ValueError('Empty content item')
        return ''.join(result)

    def content_to_sample_string(self, values):
        result = []
        for c in self.content:
            if c.constant is not None:
                result.append(c.constant)
            elif c.variable is not None:
                result.append(values[c.variable])
            elif c.alternatives is not None:
                result.append(c.alternatives[0])
            else:
                raise ValueError('Empty content item')
        return ''.join(result)



@dataclass
class IniRule:
    records: List[IniRuleRecord]

    def generate_section(self, intent_name):
        records = []
        records.append(f'[{intent_name}]')
        headers = Query.en(self.records).select_many(lambda z: z.headers.items()).distinct(lambda z: z[0]).to_list()
        for key, values in headers:
            records.append(f'{key} = {"|".join(values)}')
        contents = Query.en(self.records).select(lambda z: z.content_to_ini()).distinct().to_list()
        records.extend(contents)
        return '\n'.join(records)

    def to_sample_str(self, values):
        key = tuple(sorted(values))
        for rec in self.records:
            if key == rec.var_code:
                c = rec.content_to_sample_string(values)
                return c
        raise ValueError(f"Could not find a rule with variables {key}")







class ToIni(WalkerState):
    def __init__(self):
        self.previous = None #type: Optional['ToIni']
        self.current_key = () #type: Tuple[str,...]
        self.content = None #type: Optional[Content]
        self.header = None #type: Optional[Tuple[str, List[str]]]

    def spawn(self, **kwargs):
        return self._spawn(kwargs, content = None, header = None)


    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Union[Iterable['WalkerState'], 'WalkerState.SkipPush']:
        if name is not None:
            yield self.spawn(current_key = self.current_key+(name,))
        else:
            yield self

    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        if name is not None:
            yield self.spawn(current_key = self.current_key[:-1])
        else:
            yield self


    def on_constant(self, binding: DubBinding, dub: ConstantDub) -> Iterable['WalkerState']:
        yield self.spawn(content=Content(constant=dub.value))

    def on_set(self, binding: DubBinding, dub: SetDub) -> Iterable['WalkerState']:
        if binding.produces_value:
            var_name = '_'.join(self.current_key) + '_' + binding.name
            yield self.spawn(
                content=Content(variable=var_name),
                header=(var_name, list(dub.str_to_value()))
            )
        else:
            yield self.spawn(
                content=Content(alternatives=list(dub.str_to_value())),
            )


    def collect(self):
        headers = (self
                   .back_iterate(lambda z: z.previous)
                   .select(lambda z: z.header)
                   .where(lambda z: z is not None)
                   .to_dictionary(lambda z: z[0], lambda z: list(z[1]))
                   )
        content = (self
                   .back_iterate(lambda z: z.previous)
                   .select(lambda z: z.content)
                   .where(lambda z: z is not None)
                   .feed(list,reversed,list)
                   )
        return IniRuleRecord(
            headers,
            content,
            tuple(sorted(headers))
        )

    def postprocess(self, iter: Iterable):
        records = list(iter)
        return IniRule(records)








