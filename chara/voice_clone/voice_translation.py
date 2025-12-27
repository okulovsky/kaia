from chara.common import ICache, ListCache, logger
from chara.common.tools import Wav
from chara.voice_clone.common import VoiceInference, VoiceTrain
from .voice_clone import VoiceCloneCache
from pathlib import Path
from dataclasses import dataclass

@dataclass
class VoiceCloner:
    train: VoiceTrain
    inference: VoiceInference


class VoiceTranslationCache(ICache[Wav.List]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.generations = ListCache[VoiceCloneCache, Wav.List](VoiceCloneCache)

    def pipeline(self,
                 source: Path,
                 texts: list[str],
                 steps: list[VoiceCloner]
                 ):
        @logger.phase(self.generations)
        def _():
            generation_source = source
            wavs = Wav.List()
            for i, step in enumerate(steps):
                subcache = self.generations.create_subcache(i)
                @logger.phase(subcache)
                def __():
                    subcache.pipeline(
                        generation_source,
                        step.train,
                        texts,
                        step.inference
                    )

                generation_source = subcache.inference.voiceover.files.working_folder
                result = subcache.read_result()
                result.assign_metakey('generation', i)
                wavs+=result

            self.generations.write_result(wavs)

        wavs = self.generations.read_result()
        self.write_result(wavs)







