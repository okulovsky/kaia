from kaia.eaglesong.core import Listen
from enum import Enum



class AudioControlListen(Listen):
    class NLU(Enum):
        Rhasspy = 0
        Whisper = 1

    def __init__(self,
                 open_mic: bool = False,
                 nlu: 'AudioControlListen.NLU' = None,
                 whisper_prompt: None|str = None
                 ):
        if nlu is None:
            nlu = AudioControlListen.NLU.Rhasspy
        self.open_mic = open_mic
        self.nlu = nlu
        self.whisper_prompt = whisper_prompt

