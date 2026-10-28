from grammatron import TemplateBase, AStarParser
from .recognition_setup import RecognitionResult, IPostprocessor

class FreeSpeechPostprocessor(IPostprocessor):
    def __init__(self, template: TemplateBase|None):
        self.template = template

    def postprocess(self, result):
        try:
            if self.template is None:
                recognized = result
            else:
                parser = AStarParser(self.template.dub)
                result = parser.parse(result)
                recognized = self.template(result)
        except Exception as exception:
            return RecognitionResult(None, result, exception)
        return RecognitionResult(recognized, result)
