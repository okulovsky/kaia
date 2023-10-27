from typing import *
from ..structures import DubBinding, UnionDub, SequenceDub, ConstantDub, SetDub
from abc import ABC, abstractmethod
from yo_fluq_ds import Query
from copy import copy



class WalkerState(ABC):
    class SkipPush:
        def __init__(self, state: 'WalkerState'):
            self.state = state

    def on_constant(self, binding: DubBinding, dub: ConstantDub) -> Iterable['WalkerState']:
        return (self,)

    def on_set(self, binding: DubBinding, dub: SetDub) -> Iterable['WalkerState']:
        return (self,)

    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable[Union['WalkerState', 'WalkerState.SkipPush']]:
        return (self,)

    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        return (self,)

    def postprocess(self, iter: Iterable):
        return Query.en(iter)

    @abstractmethod
    def collect(self):
        pass

    def _back_iterate(self, selector):
        item = self
        while item is not None:
            yield item
            item = selector(item)

    def back_iterate(self, selector):
        return Query.en(self._back_iterate(selector))

    def stack_back_iterate(self, previous, level):
        items = []
        stack_parent = None
        self_level = level(self)
        for item in self.back_iterate(lambda z: z.previous):
            if item.stack_level == self_level:
                items.append(item)
            elif item.stack_level == self_level - 1:
                stack_parent = item
                break
            else:
                raise ValueError(f"Unexpected parent's stack_level {item.stack_level} (the current is {self_level})")
        if stack_parent is None and self_level>0:
            raise ValueError(f'Cannot find stack parent for {self_level}')
        return items, stack_parent

    def _spawn(self, specified: Dict[str, Any], **default):
        obj = copy(self)
        obj.previous = self
        for k, v in default.items():
            if not hasattr(obj, k):
                raise ValueError(f"key {k} is missing from object {obj}")
            setattr(obj, k, v)
        for k, v in specified.items():
            if not hasattr(obj, k):
                raise ValueError(f"key {k} is missing from object {obj}")
            setattr(obj, k, v)
        return obj




    def value_for_template(self, items, key_value_selector, template):
        value = Query.en(items).select(key_value_selector).where(lambda z: z is not None).to_dictionary(lambda z: z[0], lambda z: z[1])
        if template.dict_to_value is not None:
            value = template.dict_to_value(value)
        return value




    def _walk(self: 'WalkerState', template: UnionDub) -> Iterable:
        for state in WalkerState._walk_template(self, template, None):
            collection = state.collect()
            if collection is not None:
                yield collection

    def walk(self, template: UnionDub):
        return self.postprocess(self._walk(template))

    def _walk_template(self: 'WalkerState', template: UnionDub, name) -> Iterable['WalkerState']:
        for sequence in template.sequences:
            push = self.push(name, template, sequence)
            for sequence_state in push:
                if isinstance(sequence_state, WalkerState.SkipPush):
                    yield sequence_state.state
                else:
                    for state in WalkerState._walk_sequence(sequence_state, sequence, len(sequence.steps)-1):
                        for end_state in state.pop(name, template, sequence):
                            yield end_state

    def _walk_sequence(self: 'WalkerState', sequence: SequenceDub, step_index: int) -> Iterable['WalkerState']:
        if step_index == -1:
            yield self
            return

        step = sequence.steps[step_index]
        for state in WalkerState._walk_sequence(self, sequence, step_index-1):
            if isinstance(step.type, UnionDub):
                yield from WalkerState._walk_template(state, step.type, step.name)
            elif isinstance(step.type, SequenceDub):
                raise ValueError('Sequence cannot be another sequence without template')
            elif isinstance(step.type, ConstantDub):
                yield from state.on_constant(step, step.type)
            elif isinstance(step.type, SetDub):
                yield from state.on_set(step, step.type)
            else:
                raise ValueError('Step was neither UnionDub, SequenceDub, ConstantDub or SetDub')
