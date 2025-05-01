from ..brainbox_mapping import BrainBoxMapping
from ...prompters import IPrompter
from ..applicator import IApplicator
from ...parsers import IParser
from ..object_to_task import PromptBasedObjectConverter
from brainbox import BrainBox
from .step import IStep, IStepFactory

class BrainBoxMappingStep(IStep):
    def __init__(self, api: BrainBox.Api, mapping: BrainBoxMapping):
        self.api = api
        self.mapping = mapping

    def process(self, history, current):
        return self.mapping.create(current).execute(self.api)

    def shorten(self, data):
        return data.result


class PromptMappingStepFactory(IStepFactory):
    def __init__(self, api: BrainBox.Api, prompter: IPrompter, model: str, applicator: IApplicator, parser: IParser|None = None):
        self.api = api
        self.prompter = prompter
        self.model = model
        self.applicator = applicator
        self.parser = parser

    def create_step(self) -> IStep:
        return BrainBoxMappingStep(
            self.api,
            BrainBoxMapping(
                PromptBasedObjectConverter(
                    self.prompter,
                    self.model,
                ),
                self.applicator,
                self.parser
            )
        )