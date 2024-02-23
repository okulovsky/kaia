from ..core.algorithms.walker_state import *
from ..core.utils.startswith import Startswith
from copy import copy

DEBUG = False

class Decomposer(WalkerState):
    def __init__(self,
                 s: str,
                 voc: Dict[str, Dict[str, Any]],
                 ):
        self.s = s
        self.voc = voc
        self.index = 0
        self.stack_level = 0
        self.template_name = None #type: Optional[str]
        self.sequence = () #type: Tuple[str,...]
        self.previous = None #type: Optional['Decomposer']

    def spawn(self, **kwargs) -> 'Decomposer':
        obj = self._spawn(kwargs, sequence = ())
        if not isinstance(obj.sequence, tuple):
            raise ValueError(f'Sequence has to be tuple, but was {type(obj.sequence)}, {obj.sequence}')
        return obj

    def on_constant(self, binding: DubBinding, dub: ConstantDub) -> Iterable['WalkerState']:
        sw = Startswith(self.s, self.index)
        ind = sw.startswith(dub.value)
        if DEBUG:
            print(f'[CONSTANT] {self.s[self.index:]} {dub.value} {ind}')
        if ind is not None:
            if self.template_name not in self.voc:
                raise ValueError(f'Template {self.template_name} is missing from vocabulary')
            if dub.value not in self.voc[self.template_name]:
                raise ValueError(f'Value for `{dub.value} is missing from template {self.template_name} in vocabulary')
            to = self.voc[self.template_name][dub.value]
            yield self.spawn(index=ind, sequence=(to,))


    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable[Union['WalkerState', 'WalkerState.SkipPush']]:
        yield self.spawn(stack_level = self.stack_level+1, template_name = template.get_name())

    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        track, parent = self.stack_back_iterate(lambda z: z.previous, lambda z: z.stack_level)
        sequence = Query.en(track).select(lambda z: z.sequence).feed(tuple,reversed, Query.en).select_many(lambda z: z).to_tuple()
        yield parent.spawn(sequence=sequence, index=self.index)

    def on_set(self, binding: DubBinding, dub: SetDub) -> Iterable['WalkerState']:
        front = [(self.index, ())]
        i = 0
        while i<len(front):
            ind, path = front[i]
            i+=1
            if len(path)!=0:
                yield self.spawn(index=ind, sequence=path)
            sw = Startswith(self.s, ind)
            if dub.get_name() not in self.voc:
                raise ValueError(f"Set {dub.get_name()} is missing from vocabulary")
            for word, file in self.voc[dub.get_name()].items():
                new_ind = sw.startswith(word)
                if DEBUG:
                    print(f'[SET] {self.s[ind:]} {word} {new_ind}')
                if new_ind is None:
                    continue
                front.append((new_ind, path+(file,)))



    def collect(self):
        remainder = self.s[self.index:].strip()
        if DEBUG:
            print(f'[COLLECT] {self.index} {self.s} `{remainder}`')
        if len(remainder) == 0:
            return self.back_iterate(lambda z: z.previous).select(lambda z: z.sequence).feed(tuple,reversed, Query.en).select_many(lambda z: z).to_list()
        return None











