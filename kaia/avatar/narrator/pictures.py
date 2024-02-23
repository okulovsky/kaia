from typing import *
from kaia.brainbox import BrainBoxTaskPack, BrainBoxTask, MediaLibrary, DownloadingPostprocessor
from kaia.avatar.dub.core import Template
from copy import deepcopy
from uuid import uuid4

class PictureTaskGenerator:
    def __init__(self,
                 prompt_template: Template,
                 brain_box_task_template: Optional[BrainBoxTask] = None,
                 collecting_task_template: Optional[BrainBoxTask] = None,
                 values_to_model: Optional[Callable[[Dict], str]] = None,
                 values_to_negative: Optional[Callable[[Dict], str]] = None
                 ):
        self.prompt_template = prompt_template
        if brain_box_task_template is not None:
            self.brain_box_task_template = brain_box_task_template
        else:
            self.brain_box_task_template = BrainBoxTask(
                id = '',
                decider = 'Automatic1111',
                arguments={},
            )
        if collecting_task_template is not None:
            self.collecting_task_template = collecting_task_template
        else:
            self.collecting_task_template = BrainBoxTask(
                id='',
                decider='Collector',
                arguments={},
            )
        self.values_to_model = values_to_model
        self.values_to_negative = values_to_negative

    def generate_task(self, value: Dict) -> BrainBoxTask:
        prompt = self.prompt_template.to_str(value)
        task = deepcopy(self.brain_box_task_template)
        task.arguments['prompt'] = prompt
        if self.values_to_negative is not None:
            task.arguments['negative_prompt'] = self.values_to_negative(value)
        if self.values_to_model is not None:
            task.decider_parameters = self.values_to_model(value)
        id = 'id_' + str(uuid4()).replace('-', '')
        task.id = id
        return task


    def generate_task_pack(self, tag_values: List[Dict]) -> BrainBoxTaskPack:
        intermediate = []
        dependencies = {}
        tags = {}
        for value in tag_values:
            task = self.generate_task(value)
            tags[task.id] = value
            dependencies[task.id] = task.id
            intermediate.append(task)

        collect = deepcopy(self.collecting_task_template)
        collect.id = str(uuid4())
        collect.arguments = {'tags': tags}
        collect.dependencies = dependencies

        return BrainBoxTaskPack(
            collect,
            tuple(intermediate),
            DownloadingPostprocessor(opener=MediaLibrary.read)
        )


