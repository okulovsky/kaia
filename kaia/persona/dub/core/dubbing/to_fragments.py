from dataclasses import dataclass
from ..algorithms.walker_state import *
from ..structures import Dub, ConstantDub, SetDub
from ..templates import Template
from enum import Enum
from .dto import DubbingSequence, DubbingFragment, FragmenterSettings

@dataclass
class FragmenterResponse:
    sequences: List[DubbingSequence]
    required_dubs: List[Dub]



class ToFragments(WalkerState):
    def __init__(self,
                 settings: FragmenterSettings,
                 ):
        self.settings = settings
        self.previous = None #type: Optional['ToFragments']
        self.dub_name = None #type: Optional[str]
        self.fragments = () #type: Tuple[DubbingFragment, ...]
        self.requirement = None #type: Optional[Dub]

    def spawn(self, **kwargs):
        return self._spawn(kwargs, fragments = (), requirement = None)

    def collect(self):
        sequence = self.back_iterate(lambda z: z.previous).select(lambda z: z.fragments).feed(tuple,reversed,Query.en).select_many(lambda z: z).to_tuple()
        required = self.back_iterate(lambda z: z.previous).select(lambda z: z.requirement).where(lambda z: z is not None).distinct(lambda z: z.get_name()).to_list()
        return FragmenterResponse(
            [DubbingSequence(sequence)],
            required
        )

    def postprocess(self, iter: Iterable[FragmenterResponse]):
        iter = list(iter)
        sequences = Query.en(iter).select_many(lambda z: z.sequences).to_list()
        required = Query.en(iter).select_many(lambda z: z.required_dubs).distinct(lambda z: z.get_name()).to_list()

        return FragmenterResponse(
            sequences,
            required
            )

    def frag(self, s):
        return DubbingFragment(self.dub_name, s, False)

    def holder(self, s):
        return DubbingFragment(self.dub_name, s, True)

    def on_constant(self, binding: DubBinding, dub: ConstantDub) -> Iterable['WalkerState']:
        yield self.spawn(fragments = (self.frag(dub.value),))

    def on_set(self, binding: DubBinding, dub: SetDub) -> Iterable['WalkerState']:
        yield self.spawn(fragments=(self.holder(dub.to_str(dub.get_placeholder_value())),), requirement=dub)
        return
        #TODO: the following code is for inline dubbing, when the short options (e.g. Plural Agreeement)
        #are dubbed inside the string to increase quality. This brings problems right now:
        #As the dub name is dub.get_name() and not self.dub_name(), it won't work anyway. This needs to be revised if we want to continue with inline dubbing
        if len(dub.str_to_value()) <= self.settings.max_values_to_go_inline:
            fragments = []
            for i, val in enumerate(dub.str_to_value()):
                v = (' ' if i > 0 else '')+val
                fragments.append(DubbingFragment(dub.get_name(), v, False))
            yield self.spawn(fragments = tuple(fragments))
        else:
            yield self.spawn(fragments = (self.holder(dub.to_str(dub.get_placeholder_value())),), requirement = dub)

    def push(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        t = Template('{value}',value=template)
        short = t.get_placeholder_value()
        short_str = t.to_str(short)
        if name is None:
            yield self.spawn(dub_name = template.get_name())
        else:
            yield WalkerState.SkipPush(self.spawn(
                fragments = (self.holder(short_str),),
                requirement = template
            ))

    def pop(self, name: Optional[str], template: UnionDub, sequence: SequenceDub) -> Iterable['WalkerState']:
        yield self


