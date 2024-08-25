from typing import *
from kaia.brainbox import BrainBoxTaskPack, BrainBoxTask, MediaLibrary, DownloadingPostprocessor
from kaia.brainbox.deciders import Collector
from kaia.dub.core import Template
from copy import deepcopy
from uuid import uuid4
from functools import partial

class PictureTaskGenerator:
    def __init__(self,
                 prompt_template: Template,
                 task_decider: Optional = None,
                 collecting_decider: Optional = None,
                 values_to_model: Optional[Callable[[Dict], str]] = None,
                 values_to_negative: Optional[Callable[[Dict], str]] = None
                 ):
        self.prompt_template = prompt_template
        self.task_decider = task_decider if task_decider is not None else 'Automatic1111'
        self.collecting_decider = collecting_decider if collecting_decider is not None else Collector.to_media_library
        self.values_to_model = values_to_model
        self.values_to_negative = values_to_negative

    def generate_task(self, value: Dict) -> BrainBoxTask:
        prompt = self.prompt_template.to_str(value)
        task = BrainBoxTask(
            decider=self.task_decider,
            arguments = dict(prompt=prompt),
        )
        if self.values_to_negative is not None:
            task.arguments['negative_prompt'] = self.values_to_negative(value)
        if self.values_to_model is not None:
            task.decider_parameters = self.values_to_model(value)
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

        collect = BrainBoxTask(
            decider=self.collecting_decider,
            arguments=dict(tags=tags),
            dependencies = dependencies
        )

        return BrainBoxTaskPack(
            collect,
            tuple(intermediate),
            DownloadingPostprocessor(opener=MediaLibrary.read)
        )


