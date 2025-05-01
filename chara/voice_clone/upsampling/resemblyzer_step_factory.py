from brainbox.deciders import Resemblyzer, Collector
from brainbox import BrainBox, MediaLibrary
from pathlib import Path
from yo_fluq import *
from kaia.common import Loc
from .upsampling_item import UpsamplingItem
from brainbox import flow


class ResemblyzerStepFactory(flow.IStepFactory):
    def __init__(self, api: BrainBox.Api, model_name: str):
        self.api = api
        self.model_name = model_name

    def get_training_command(self, folders: list[Path]):
        records = []
        for folder in folders:
            for file in Query.folder(folder):
                records.append(MediaLibrary.Record(
                    file.name,
                    folder,
                    tags=dict(text='', split='train', speaker=folder.name)
                ))
        ml = MediaLibrary(tuple(records), ())
        fname = Loc.temp_folder/f'resemblyzer_dataset_{self.model_name}.zip'
        ml.save(fname)
        upload = Resemblyzer.upload_dataset(self.model_name, fname, False)
        task = BrainBox.Task.call(Resemblyzer).train(self.model_name)
        return BrainBox.Command(BrainBox.ExtendedTask(task, upload))

    def convert(self, item: UpsamplingItem):
        return flow.IObjectConverter.Output(BrainBox.Task.call(Resemblyzer).distances(item.voiceover_file, self.model_name))

    def create_step(self) -> flow.IStep:
        return flow.BrainBoxMappingStep(
            self.api,
            flow.BrainBoxMapping(
                flow.FunctionalObjectToTask(self.convert),
                flow.SimpleApplicator(flow.Address('resemblyzer')),
                flow.FunctionalParser(self.to_df)
            )
        )

    def to_df(self, rec):
        return (
            Query.en(rec)
            .group_by(lambda z: z['speaker'])
            .to_dictionary(lambda z: z.key, lambda z: min(x['score'] for x in z.value))
        )


