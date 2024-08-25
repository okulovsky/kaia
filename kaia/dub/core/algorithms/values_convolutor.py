from typing import *
from .walker_state import WalkerState
from ...core import UnionDub, SequenceDub, IDubBinding, SetDub, ConstantDub
from dataclasses import dataclass
import traceback


class ValuesConvolutor(WalkerState):
    def __init__(self, values: Dict):
        self.values = values
        self.prev_level = None
        self.level: int = 0
        self.prefix: Tuple[str, ...] = ()
        self.collected: Tuple[Tuple[str, Any], ...] = ()
        self.used: Tuple[str, ...] = ()

    def pr(self, info, add=None):
        if False:
            s = '  ' * self.level
            s += '[' + info + '] '
            s += '_'.join(self.prefix)
            if add is not None:
                s += '         ' + str(add)
            print(s)
        return self

    def spawn(self, **kwargs):
        return self._spawn(kwargs)

    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Union[
        Iterable['WalkerState'], 'WalkerState.SkipPush']:
        if name is not None:
            yield self.spawn(
                prev_level=self,
                level=self.level + 1,
                prefix=self.prefix + (name,),
                collected=()
            ).pr('PUSH', sequence.get_name())
        else:
            yield self.spawn(previous=self, level=self.level + 1).pr('ZERO PUSH', sequence.get_name())

    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        if name is None:
            yield self.pr('ZERO POP')
        else:
            dct = {k: v for k, v in self.collected}
            value = dct
            if template.dict_to_value is not None:
                try:
                    value = template.dict_to_value(dct)
                except:
                    value = None
            if value is not None:
                yield self.prev_level.spawn(
                    collected=self.prev_level.collected + ((name, value),),
                    used=self.used
                ).pr('POP', value)

    def on_constant(self, binding: IDubBinding, dub: ConstantDub) -> Iterable['WalkerState']:
        yield self

    def on_set(self, binding: IDubBinding, dub: SetDub) -> Iterable['WalkerState']:
        if binding.produces_value:
            var_name = '_'.join(self.prefix) + '_' + binding.name
            if var_name in self.values:
                text_value = self.values[var_name]
                if text_value in dub.str_to_value():
                    value = dub.str_to_value()[text_value]
                    yield self.spawn(
                        collected=self.collected + ((binding.name, value),),
                        used=self.used + (var_name,)
                    ).pr('SUCC', var_name)
            else:
                self.pr('FAIL', var_name)
        else:
            yield self

    def collect(self):
        return self

    def postprocess(self, iter: Iterable):
        available = tuple(sorted(self.values))
        options = []
        for option in iter:
            if available == tuple(sorted(option.used)):
                options.append(option)

        if len(options) == 0:
            raise ValueError(f'Cannot convolute values {self.values}')
        #if len(options) > 1:
            #raise ValueError(f'Ambiguous parsing with values {self.values}')
        value = {k: v for k, v in options[0].collected}
        return value