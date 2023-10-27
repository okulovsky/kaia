from typing import *
from .walker_state import WalkerState
from ..structures import UnionDub, SequenceDub, DubBinding, ConstantDub, SetDub
from ..utils.startswith import Startswith
from copy import copy

DEBUG = False

class Parser(WalkerState):
    def __init__(self, s: str):
        self.s = s
        self.index = 0
        self.stack_command = None #type: Optional[Tuple[str, Any]]
        self.stack_level = 0
        self.previous = None

    def spawn(self, **kwargs):
        return self._spawn(kwargs, stack_command = None)


    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Union[Iterable['WalkerState'], WalkerState.SkipPush]:
        yield self.spawn(stack_level = self.stack_level+1)


    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        if name is None: #Template may ends only if the rest of the string is space
            for i in range(self.index, len(self.s)):
                if not self.s[i].isspace():
                    return
        stack, stack_parent = self.stack_back_iterate(lambda z: z.previous, lambda z: z.stack_level)
        value = self.value_for_template(stack, lambda z: z.stack_command, template)
        yield stack_parent.spawn(stack_command = (name, value), index = self.index)

    def on_constant(self, binding: DubBinding, type: ConstantDub) -> Iterable['WalkerState']:
        if DEBUG:
            print(f'CONST: `{self.s[self.index:]}` `{type.value}`')

        new_index = Startswith(self.s, self.index).startswith(type.value)
        if new_index is not None:
            yield self.spawn(index = new_index)

    def on_set(self, binding: DubBinding, dub: SetDub) -> Iterable['WalkerState']:
        if DEBUG:
            print(f'SET: `{self.s[self.index:]}` `{list(dub.str_to_value())}`')
        sw = Startswith(self.s, self.index)
        for s,value in dub.str_to_value().items():
            new_index = sw.startswith(s)
            if new_index is not None:
                kv_pair = (binding.name, value)
                if not binding.produces_value:
                    kv_pair = None
                yield self.spawn(index = new_index, stack_command = kv_pair)

    def collect(self):
        return (self
                .back_iterate(lambda z: z.previous)
                .select(lambda z: z.stack_command)
                .where(lambda z: z is not None and z[0] is None)
                .select(lambda z: z[1])
                .first()
                )

