from typing import *
from abc import ABC, abstractmethod
from kaia.brainbox.core import BrainBoxTask, BrainBoxWebApi
from dataclasses import dataclass
from kaia.infra import FileIO
import re


@dataclass
class BrainBoxTestCaseReportSection:
    data: Any
    validation_errors: None | str


class BrainBoxTestCase(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def generate_tasks(self) -> Iterable[BrainBoxTask]:
        pass

    @abstractmethod
    def validate_and_get_report_section(self, generated_tasks: Tuple[BrainBoxTask, ...],
                                        api: BrainBoxWebApi) -> BrainBoxTestCaseReportSection:
        pass

    def draw_section(self, section: BrainBoxTestCaseReportSection):
        pass


class DubbingBrainBoxTestCase(BrainBoxTestCase):
    def __init__(self,
                 name: str,
                 outputs_count: int,
                 dubbing_task: BrainBoxTask,
                 ):
        self.name = name
        self.outputs_count = outputs_count
        self.dubbing_task = dubbing_task

    def get_name(self) -> str:
        return self.name


    def generate_tasks(self) -> Iterable[BrainBoxTask]:
        tasks = [self.dubbing_task]

        for i in range(self.outputs_count):
            translation_task = BrainBoxTask(
                BrainBoxTask.safe_id(),
                'OutputTranslator',
                arguments=dict(take_array_element=i),
                dependencies=dict(input=self.dubbing_task.id)
            )
            tasks.append(translation_task)

            tasks.append(BrainBoxTask(
                BrainBoxTask.safe_id(),
                'Whisper',
                decider_method='transcribe_text_only',
                arguments={},
                dependencies=dict(filename=translation_task.id)
            ))
        return tasks

    def _simplify(self, s):
        return re.sub('[^a-zA-Z]', '', s.lower())

    def validate_and_get_report_section(self, generated_tasks: Tuple[BrainBoxTask, ...],
                                        api: BrainBoxWebApi) -> BrainBoxTestCaseReportSection:
        section = {}
        section['source_text'] = generated_tasks[0].arguments['text']
        src = self._simplify(section['source_text'])
        result = api.get_result(generated_tasks[0].id)

        if result is None:
            return BrainBoxTestCaseReportSection(section, "Task does not have result")

        validation_errors = []
        section['outputs'] = []
        for i in range(self.outputs_count):
            section['outputs'].append(FileIO.read_bytes(api.download(result[i])))
            recognized = api.get_result(generated_tasks[2*i+1+1].id)
            if recognized is None:
                validation_errors.append(f'No result for output #{i}')
            if not isinstance(recognized, str):
                validation_errors.append(f'Result for output #{i} is not string')

            txt = self._simplify(recognized)
            if txt!=src:
                validation_errors.append(f'Result for output #{i} is wrong, recognized: `{recognized}`')

        return BrainBoxTestCaseReportSection(section, '\n'.join(validation_errors))

    def draw_section(self, section: BrainBoxTestCaseReportSection):
        from ipywidgets import VBox, Label, Audio

        ar = [Label('Text for voiceover: ' + section.data['source_text'])]

        for output in section.data['outputs']:
            ar.append(Audio(value=output, autoplay=False))

        ar.append(Label(section.validation_errors if section.validation_errors else ''))
        return VBox(ar)

