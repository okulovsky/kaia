from chara.common import ICache, logger
from chara.common.tools import Wav
from chara.voice_clone.common import VoiceTrain, VoiceInference, VoiceSimilarityCache
from pathlib import Path

class ExploringCache(ICache[Wav.List]):
    def __init__(self, work_folder: Path|None = None):
        super().__init__(work_folder)
        self.training = VoiceTrain.Cache()
        self.inference = VoiceInference.Cache()
        self.similarity = VoiceSimilarityCache()

    def pipeline(self,
                 sources: Path|list[Path],
                 trainers: VoiceTrain|list[VoiceTrain],
                 texts: str|list[str],
                 inferences: VoiceInference|list[VoiceInference],
                 ):

        @logger.phase(self.training)
        def _():
            VoiceTrain.pipeline(
                self.training,
                trainers,
                sources
            )

        models = self.training.read_result()

        @logger.phase(self.inference)
        def _():
            VoiceInference.pipeline(
                self.inference,
                inferences,
                models,
                texts
            )

        @logger.phase(self.similarity)
        def _():
            index_to_sample = {}
            for index, subcache in enumerate(self.training.preprocessing.read_subcaches()):
                index_to_sample[index] = subcache.recoded.read_paths()

            candidate_to_index = {}
            inference = self.inference.read_result()
            for wav in inference.wavs:
                candidate_to_index[wav.path] = wav.metadata['model_index']

            self.similarity.pipeline(
                index_to_sample,
                candidate_to_index
            )

        similarities = self.similarity.read_result()

        inference_result = self.inference.read_result()

        for wav in inference_result.wavs:
            v = similarities.get(wav.path, None)
            if v is not None:
                wav.metadata['similarity'] = v.best_distance
            wav.metadata['train'] = False

        train_samples = self.training.read_train_samples()
        for wav in train_samples.wavs:
            wav.metadata['train'] = True

        self.write_result(
            train_samples + inference_result
        )








