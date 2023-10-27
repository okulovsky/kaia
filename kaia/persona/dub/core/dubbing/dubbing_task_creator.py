from .dto import *
from uuid import uuid4
from .....brainbox import BrainBoxTask
from copy import copy
from yo_fluq_ds import *
from .dubbing_pack import DubbingPack
from .fragmenter import Fragmenter, FragmenterSettings, Dub, Template
from .optimizer import optimize_sequences


class DubbingTaskCreator:
    def __init__(self, settings: FragmenterSettings = FragmenterSettings()):
        self.settings = settings

    def fragment(self, predefined_dubs: Iterable[Dub], template: Iterable[Template], voice: str):
        return Fragmenter(predefined_dubs, template, self.settings).run(voice)

    def optimize_sequences(self, sequences: List[DubbingSequence]):
        return optimize_sequences(sequences, self.settings.max_sequence_length, self.settings.min_sequence_length)

    def create_dub_and_cut_tasks(self, sequences: List[DubbingSequence]):
        tasks = []
        for sequence in sequences:
            text = []
            length = 0
            cuts = []
            voice = None
            for fragment in sequence.fragments:
                voice = fragment.voice
                total_text = fragment.prefix+fragment.text+fragment.suffix
                ln = len(total_text)
                if not fragment.is_placeholder:
                    cuts.append(CutSpec(length, ln, fragment))
                text.append(total_text)
                length += ln
            tasks.append(DubAndCutTask(cuts, ''.join(text), voice))
        return tasks

    def create_mock_fragments(self, sequences: List[DubbingSequence], to_lowercase = False):
        tasks = self.create_dub_and_cut_tasks(sequences)
        result = []
        for task in tasks:
            for cut in task.cuts:
                frag = copy(cut.info)
                frag.voice = task.voice
                frag.file_name = task.text[cut.start:cut.start+cut.length]
                if to_lowercase:
                    frag.file_name = frag.file_name.lower()
                frag.option_index = 0
                result.append(frag)
        return result




    @staticmethod
    def _uid():
        return 'id_'+str(uuid4()).replace('-','')



    def create_tasks(self, tasks: List[DubAndCutTask],
                     dubber_name: str,
                     dubber_method_name: str,
                     batch: str,
                     collector_name: str = 'DubCollector',
                     collector_method_name: str = 'collect',
                     back_track: str = 'Dubbing'
                     ):
        collector_args = {}
        dub_tasks = []
        dependencies = {}

        for task in tasks:
            id = DubbingTaskCreator._uid()
            dub_tasks.append(BrainBoxTask(
                id,
                dubber_name,
                dubber_method_name,
                arguments=dict(voice = task.voice, text=task.text),
                batch = batch
            ))
            dependencies[id]=id
            cuts = []
            for cut in task.cuts:
                if cut.info.is_placeholder:
                    continue
                cuts.append(cut)
            collector_args[id] = cuts

        dub_tasks.append(BrainBoxTask(
            str(uuid4()),
            collector_name,
            collector_method_name,
            arguments=dict(spec=collector_args),
            dependencies=dependencies,
            batch=batch,
            back_track=back_track
        ))

        return dub_tasks


    def get_sequences_missing_from_pack(self, sequences: List[DubbingSequence], pack: DubbingPack):
        idx = set((f.dub, f.text, f.voice) for f in pack.fragments)
        #print(idx)
        new_sequences = []
        for sequence in sequences:
            for frag in sequence.fragments:
                if frag.is_placeholder:
                    continue
                key = (frag.dub, frag.text, frag.voice)
                if key not in idx:
                    new_sequences.append(sequence)
                    break
        return new_sequences







