from grammatron import TemplateBase, AStarParser
from brainbox import IPostprocessor
from .recognition_setup import STTConfirmation

class FreeSpeechPostprocessor(IPostprocessor):
    def __init__(self, template: TemplateBase|None):
        self.template = template

    def postprocess(self, result, api):
        try:
            if self.template is None:
                recognized = result
            else:
                parser = AStarParser(self.template.dub)
                result = parser.parse(result)
                recognized = self.template(result)
        except Exception as exception:
            return STTConfirmation(None, result, exception)
        return STTConfirmation(recognized, result)
