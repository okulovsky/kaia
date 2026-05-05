from chara.voice_clone.common import VoiceTrain, VoiceInference
from pathlib import Path


# VoiceDatasetPipeline depends on chara.voice_clone which has not yet been
# converted to the Chara pattern. This file should be revisited when
# VoiceTrain.pipeline and VoiceInference.pipeline are updated.
class VoiceDatasetPipeline:
    def __init__(self,
                 sources: list[Path],
                 voice_train: VoiceTrain,
                 voice_inference: VoiceInference,
                 lines: list[str],
                 ):
        self.voice_train = voice_train
        self.voice_inference = voice_inference
        self.lines = lines
        self.sources = sources
