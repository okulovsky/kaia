from eaglesong import Listen
from grammatron import TemplateBase
from avatar.daemon import OpenMicCommand, FreeSpeechRecognitionRequest, TemplatesRecognitionRequest

class FreeSpeechListen(Listen):
    def __init__(self, language: str|None = None, prompt: str|None = None, template: TemplateBase|None = None):
        super().__init__(
            FreeSpeechRecognitionRequest(language, prompt, template),
            OpenMicCommand()
        )


class ContextListen(Listen):
    def __init__(self, context: str):
        super().__init__(
            TemplatesRecognitionRequest(context),
            OpenMicCommand()
        )
