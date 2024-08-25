from typing import *
from .walker_state import WalkerState
from ..structures import UnionDub, SequenceDub, SetDub, IDubBinding, ConstantDub, ToStrDub
from yo_fluq import *

class ToStr(WalkerState):
    def __init__(self, value):
        self.value = {None:value}
        self.stack_level = 0
        self.fragment = None #type: Optional[str]
        self.previous = None #type: Optional['ToStr']
        self.final_response = None #type: Optional[str]
        self.error = None #type: Optional[str]


    def spawn(self, **kwargs):
        return self._spawn(kwargs, fragment = None, final_response = None)


    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        if self.error is not None:
            return (self, )

        value = self.value[name]
        if template.value_to_dict is not None:
            value = template.value_to_dict(value)
        else:
            if not isinstance(value, dict):
                raise ValueError(
                    f'If no `value_to_dict` converter is provided, the argument must be dict, but was {value} in template {template}')

        if template.treat_none_as_missing_value:
            keys = tuple(sorted(k for k,v in value.items() if v is not None))
        else:
            keys = tuple(sorted(value))

        if template.strict_dict_equality_in_to_str:
            if sequence.consumed_keys != keys:
                extra_keys = [k for k in keys if k not in sequence.consumed_keys]
                missing_keys = [k for k in sequence.consumed_keys if k not in keys]
                return (self.spawn(error=f'Missing key {missing_keys}, extra_keys {extra_keys}'), )
        else:
            for key in sequence.consumed_keys:
                if key not in keys:
                    missing_keys = [k for k in sequence.consumed_keys if k not in keys]
                    return (self.spawn(error=f'Missing key {missing_keys}'),)

        return (self.spawn(value = value, stack_level = self.stack_level+1), )

    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        if self.error is not None:
            yield self
            return

        stack, parent = self.stack_back_iterate(lambda z: z.previous, lambda z: z.stack_level)
        fragment = Query.en(stack).select(lambda z: z.fragment).where(lambda z: z is not None).feed(tuple, reversed, ''.join)
        if name is None:
            yield self.spawn(final_response = fragment)
        else:
            yield parent.spawn(fragment = fragment)


    def on_set(self, binding: IDubBinding, dub: SetDub) -> Iterable['WalkerState']:
        if self.error is not None:
            yield self
            return

        value = binding.get_value_to_consume(self.value)
        for value in dub.to_all_strs(value):
            yield self.spawn(fragment = value)

    def on_constant(self, binding: IDubBinding, dub: ConstantDub) -> Iterable['WalkerState']:
        if self.error is not None:
            yield self
            return

        yield self.spawn(fragment = dub.value)

    def on_to_str(self, binding: IDubBinding, dub: ToStrDub):
        if self.error is not None:
            yield self
            return

        value = binding.get_value_to_consume(self.value)
        yield self.spawn(fragment = dub.to_str(value))

    def collect(self):
        return self

    def postprocess(self, iter: Iterable):
        results = []
        errors = []
        for element in iter:
            if element.error is not None:
                errors.append(element.error)
            if element.final_response is not None:
                results.append(element.final_response)
        if len(results) == 0:
            raise ValueError("Errors\n"+"\n".join(errors))
        else:
            return Query.en(results)


    @staticmethod
    def start(value):
        return ToStr({None:value})






















