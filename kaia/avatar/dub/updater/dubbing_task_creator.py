import copy

from .dto import *
from uuid import uuid4
from ....brainbox import BrainBoxTask, BrainBoxTaskPack, MediaLibrary, DownloadingPostprocessor
from .fragmenter import Fragmenter, FragmenterSettings, Dub, Template
from .optimizer import optimize_sequences
from .dubber import Dubber
from dataclasses import dataclass


class DubbingTaskCreator:
    def __init__(self,
                 settings: FragmenterSettings = FragmenterSettings(),
                 dubbing_task_template: BrainBoxTask = None,
                 collector_task_template: BrainBoxTask = None
                 ):
        self.settings = settings
        if dubbing_task_template is None:
            dubbing_task_template = BrainBoxTask(id='', decider='TortoiseTTS', decider_method='aligned_dub', arguments={})
        self.dubbing_task_template = dubbing_task_template

        if collector_task_template is None:
            collector_task_template = BrainBoxTask(id = '', decider='DubCollector', arguments={})
        self.collector_task_template = collector_task_template




    def fragment(self, predefined_dubs: Iterable[Dub], template: Iterable[Template], voice: str) -> List[DubbingSequence]:
        return Fragmenter(predefined_dubs, template, self.settings).run(voice)

    def optimize_sequences(self, sequences: Iterable[DubbingSequence]):
        return optimize_sequences(sequences, self.settings.max_sequence_length, self.settings.min_sequence_length)

    def create_dub_and_cut_tasks(self, sequences: List[DubbingSequence]) -> List[DubAndCutTask]:
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


    def create_mock_dubber(self, fragments: Iterable[DubbingSequence]):
        voc = {}
        for sequence in fragments:
            for fragment in sequence.fragments:
                if fragment.dub not in voc:
                    voc[fragment.dub] = {}
                voc[fragment.dub][fragment.text] = fragment.text
        return Dubber(voc)



    @staticmethod
    def _uid():
        return 'id_'+str(uuid4()).replace('-','')



    def create_tasks(self, tasks: List[DubAndCutTask]) -> BrainBoxTaskPack:

        collector_args = {}
        dub_tasks = []
        dependencies = {}

        for task in tasks:
            id = DubbingTaskCreator._uid()
            dub_task = copy.deepcopy(self.dubbing_task_template)
            dub_task.id = id
            dub_task.arguments = dict(voice = task.voice, text=task.text)
            dub_tasks.append(dub_task)

            dependencies[id]=id
            cuts = []
            for cut in task.cuts:
                if cut.fragment.is_placeholder:
                    continue
                cuts.append(cut)
            collector_args[id] = cuts


        collection_task = copy.deepcopy(self.collector_task_template)
        collection_task.id = str(uuid4())
        collection_task.arguments = dict(spec=collector_args)
        collection_task.dependencies = dependencies


        return BrainBoxTaskPack(
            collection_task,
            tuple(dub_tasks),
            DownloadingPostprocessor(opener=MediaLibrary.read)
        )










