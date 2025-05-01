from brainbox import BrainBoxApi
from brainbox import flow
from .upsampling_item import UpsamplingItem


class VoiceoverStepFactory(flow.IStepFactory):
    def __init__(self,
                 api: BrainBoxApi,
                 ):
        self.api = api

    def convert(self, object: UpsamplingItem) -> 'flow.IObjectConverter.Output':
        task, tags = object.voice_cloner.create_voiceover_task_and_tags(object.text)
        return flow.IObjectConverter.Output(
            task,
            tags,
            None
        )

    def create_step(self) -> flow.IStep:
        return flow.BrainBoxMappingStep(
            self.api,
            flow.BrainBoxMapping(
                flow.FunctionalObjectToTask(self.convert),
                flow.SimpleApplicator(flow.Address('voiceover_file')),
                tags_address=flow.Address('voiceover_tags')
            )
        )


