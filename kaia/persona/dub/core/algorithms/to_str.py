from typing import *
from .walker_state import WalkerState
from ..structures import UnionDub, SequenceDub, SetDub, DubBinding, ConstantDub
from yo_fluq_ds import *

class ToStr(WalkerState):
    def __init__(self, value):
        self.value = {None:value}
        self.stack_level = 0
        self.fragment = None #type: Optional[str]
        self.previous = None #type: Optional['ToStr']
        self.final_response = None #type: Optional[str]


    def spawn(self, **kwargs):
        return self._spawn(kwargs, fragment = None, final_response = None)


    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        value = self.value[name]
        if template.value_to_dict is not None:
            value = template.value_to_dict(value)
        else:
            if not isinstance(value, dict):
                raise ValueError(
                    f'If no `value_to_dict` converter is provided, the argument must be dict, but was {value} in template {template}')

        keys = tuple(sorted(value))
        if template.strict_dict_equality_in_to_str:
            if sequence.consumed_keys != keys:
                return ()
        else:
            for key in sequence.consumed_keys:
                if key not in keys:
                    return ()

        return (self.spawn(value = value, stack_level = self.stack_level+1), )

    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        stack, parent = self.stack_back_iterate(lambda z: z.previous, lambda z: z.stack_level)
        fragment = Query.en(stack).select(lambda z: z.fragment).where(lambda z: z is not None).feed(tuple, reversed, ''.join)
        if name is None:
            yield self.spawn(final_response = fragment)
        else:
            yield parent.spawn(fragment = fragment)


    def on_set(self, binding: DubBinding, dub: SetDub) -> Iterable['WalkerState']:
        value = binding.get_value_to_consume(self.value)
        for value in dub.to_all_strs(value):
            yield self.spawn(fragment = value)

    def on_constant(self, binding: DubBinding, dub: ConstantDub) -> Iterable['WalkerState']:
        yield self.spawn(fragment = dub.value)

    def collect(self):
        return self.final_response

    @staticmethod
    def start(value):
        return ToStr({None:value})






















