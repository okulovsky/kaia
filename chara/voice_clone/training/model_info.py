import copy
from dataclasses import dataclass
import re
from brainbox import BrainBox, IPrerequisite, BrainBoxApi, CombinedPrerequisite
from brainbox.deciders import Piper, Collector, EmptyTask
from pathlib import Path
from yo_fluq import Query

class ModelUploadPrerequisite(IPrerequisite):
    def __init__(self, json, onnx):
        self.json = json
        self.onnx = onnx

    def execute(self, api: BrainBoxApi):
        api.download(self.json)
        Piper.UploadVoice(api.download(self.onnx)).execute(api)


@dataclass
class ModelInfo:
    onnx: str
    json: str
    training_id: str
    epoch: int
    step: int
    model_id: str

    @staticmethod
    def parse_training_result(result):
        models = []
        for model_dict in result:
            model = model_dict['onnx']
            match = re.match('(.+)_epoch=(\d+)-step=(\d+)\.onnx', model)
            model_name = model.replace('.onnx','')
            models.append(ModelInfo(
                model,
                model_dict['json'],
                match.group(1),
                int(match.group(2)),
                int(match.group(3)),
                model_name
            ))
        return Query.en(models).order_by(lambda z: z.epoch).to_list()

    @staticmethod
    def create_voiceover_command(text, models: list['ModelInfo'], speakers: list[int]|None = None) -> BrainBox.Command:
        collector = Collector.TaskBuilder()
        if speakers is None:
            speakers = [None]
        for model in models:
            for speaker in speakers:
                tags = copy.copy(model.__dict__)
                tags['speaker'] = speaker
                collector.append(
                    BrainBox.Task.call(Piper).voiceover(text, model.model_id, speaker=speaker),
                    tags
                )
        return BrainBox.Command(collector.to_collector_pack('to_array'))

    @staticmethod
    def create_upload_command(models: list['ModelInfo']) -> BrainBox.Command:
        reqs = [ModelUploadPrerequisite(m.json, m.onnx) for m in models]
        task = BrainBox.ExtendedTask(
            BrainBox.Task.call(EmptyTask)(),
            CombinedPrerequisite(reqs)
        )
        return BrainBox.Command(task)


    def export_to(self, api: BrainBox.Api, filepath: Path):
        api.download(self.onnx, filepath)
        api.download(self.json, filepath.parent/(filepath.name+'.json'))

