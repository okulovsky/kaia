from brainbox import flow
from ...tools import LanguageToDecider
from brainbox import BrainBox
from brainbox.deciders import Vosk

from .upsampling_item import UpsamplingItem

class VoskStepFactory(flow.IStepFactory):
    def __init__(self, api: BrainBox.Api):
        self.api = api

    def convert(self, item: UpsamplingItem):
        task = BrainBox.Task.call(Vosk).transcribe_to_array(
            item.voiceover_file,
            LanguageToDecider.map(item.voiceover_tags['language'], Vosk)
        )
        return flow.IObjectConverter.Output(task)

    def create_step(self) -> flow.IStep:
        return flow.BrainBoxMappingStep(
            self.api,
            flow.BrainBoxMapping(
                flow.FunctionalObjectToTask(self.convert),
                flow.SimpleApplicator(flow.Address('vosk'))
            )
        )