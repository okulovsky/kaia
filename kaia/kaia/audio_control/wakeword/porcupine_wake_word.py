from .wake_word import IWakeWordDetector
import pvporcupine

class PorcupineDetector(IWakeWordDetector):
    def __init__(self):
        self.porcupine = pvporcupine.create(keywords=['computer'])


    def detect(self, data: list[int]) -> bool:
        keyword_index = self.porcupine.process(data)
        if keyword_index >= 0:
            return True
