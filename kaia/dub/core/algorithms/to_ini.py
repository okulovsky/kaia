from .walker_state import *
from ..structures import ConstantDub, SetDub
from dataclasses import dataclass

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


@dataclass
class IniRule:
    records: List[IniRuleRecord]








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


    def on_constant(self, binding: IDubBinding, dub: ConstantDub) -> Iterable['WalkerState']:
        yield self.spawn(content=Content(constant=dub.value))

    def on_set(self, binding: IDubBinding, dub: SetDub) -> Iterable['WalkerState']:
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








