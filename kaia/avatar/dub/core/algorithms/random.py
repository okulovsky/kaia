from .walker_state import *
from numpy.random import RandomState
from ..structures import IRandomizableDub
class Randomizer(WalkerState):
    def __init__(self,
                 method: Callable,
                 ):
        self.method = method
        self.previous = None #type: Optional['Randomizer']
        self.stack_level = 0
        self.stack_command = None #type: Optional[Tuple[str, Any]]

    def spawn(self, **kwargs):
        return self._spawn(kwargs, stack_command = None)


    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Union[Iterable['WalkerState'], 'WalkerState.SkipPush']:
        if isinstance(template, IRandomizableDub):
            yield WalkerState.SkipPush(self.spawn(stack_command = (name, self.method(template))))
        else:
            yield self.spawn(stack_level = self.stack_level+1)


    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        stack, parent = self.stack_back_iterate(lambda z: z.previous, lambda z: z.stack_level)
        value = self.value_for_template(stack, lambda z: z.stack_command, template)
        yield parent.spawn(stack_command = (name, value))


    def on_set(self, binding: DubBinding, dub: SetDub) -> Iterable['WalkerState']:
        if binding.produces_value:
            value = self.method(binding.type)
            yield self.spawn(stack_command = (binding.name, value))
        else:
            yield self


    def collect(self):
        return (
            self
            .back_iterate(lambda z: z.previous)
            .select(lambda z: z.stack_command)
            .where(lambda z: z is not None and z[0] is None)
            .single()[1]
        )

