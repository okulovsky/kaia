from typing import *
from ..core.structures import Dub, SetDub, UnionDub
from ..core.templates import Template
from .dto import FragmenterSettings, DubbingSequence, DubbingFragment
from .to_fragments import ToFragments, FragmenterResponse
from yo_fluq import Query
import numpy as np


class Partitioner:
    def __init__(self, dub_name, settings: FragmenterSettings):
        self.dub_name = dub_name
        self.settings = settings
        self.current = [] #type: List[DubbingFragment]
        self.buffer = [] #type: List[DubbingSequence]
        self.flush()

    def flush(self):
        if len(self.current)>0:
            self.current.append(DubbingFragment('', self.settings.set_dub_closing, True))
            self.buffer.append(DubbingSequence(tuple(self.current)))
        self.current = [DubbingFragment('', self.settings.set_dub_opening, True)]

    def add(self, w):
        fragment = DubbingFragment(self.dub_name, w, False, prefix=self.settings.set_dub_prefix, suffix=self.settings.set_dub_suffix)
        ln = sum(len(f.full_text) for f in self.current) + len(fragment.full_text) + len(self.settings.set_dub_closing)
        if ln > self.settings.max_sequence_length:
            self.flush()
        self.current.append(fragment)



class Fragmenter:
    def __init__(self,
                 predefined_dubs: Iterable[Dub],
                 templates: Iterable[Template],
                 settings: Optional[FragmenterSettings] = None
                 ):
        self.settings = settings if settings is not None else FragmenterSettings()
        self.sequences = [] #type: List[DubbingSequence]
        self.processed_names = set() #type: Set[str]
        self.debt = [] #type: List[Dub]
        self.debt.extend(predefined_dubs)
        self.debt.extend(c.dub for c in templates)


    def _words_to_fragments(self, dub_name, words: List[str]):
        part = Partitioner(dub_name, self.settings)
        for word in Query.en(words).order_by(lambda z: np.random.randint(1000)):
            part.add(word)
        part.flush()
        self.sequences.extend(part.buffer)

    def process_set_with_breaking(self, dub: SetDub):
        words = set()
        for s in dub.str_to_value():
            for w in s.split(' '):
                w = w.strip()
                if w not in words and w != '':
                    words.add(w)
        words = list(sorted(words))
        self._words_to_fragments(dub.get_name(), words)

    def process_set_without_breaking(self, dub: SetDub):
        phrases = []
        words = []
        for s in dub.str_to_value():
            if ' ' in s:
                phrases.append(s)
            else:
                words.append(s)
        self._words_to_fragments(dub.get_name(), words)
        for phrase in phrases:
            fragment = DubbingFragment(dub.get_name(), phrase, False)
            sequence = DubbingSequence((fragment,))
            self.sequences.append(sequence)


    def process_union(self, union: UnionDub, allow_pop = False):
        result = ToFragments(self.settings).walk(union) #type: FragmenterResponse
        self.sequences.extend(result.sequences)
        self.debt.extend(Query.en(result.required_dubs).where(lambda z: z.get_name() not in self.processed_names))

    def process(self, item):
        if isinstance(item, UnionDub):
            self.process_union(item)
        elif isinstance(item, SetDub):
            if len(item.str_to_value()) >= self.settings.min_set_values_to_break_to_words:
                self.process_set_with_breaking(item)
            else:
                self.process_set_without_breaking(item)
        if isinstance(item, Dub):
            self.processed_names.add(item.get_name())

    def run(self, voice: str):
        i = 0
        while i<len(self.debt):
            item = self.debt[i]
            i+=1
            if isinstance(item, Dub) and item.get_name() in self.processed_names:
                continue
            self.process(item)
            if isinstance(item, Dub):
                self.processed_names.add(item.get_name())

        for sequence in self.sequences:
            for fragment in sequence.fragments:
                fragment.voice = voice

        return self.sequences










