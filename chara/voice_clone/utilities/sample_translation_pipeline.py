from chara import Chara, CaseCollection, BrainBoxCasePipeline
from chara.common.descriptions import Language
from pathlib import Path

from chara.voice_clone import VoiceTrain, VoiceInference, Revoice



class SampleTranslationPipeline:
    def __init__(self,
                 target_language: Language,
                 source: Path,
                 train: VoiceTrain,
                 inference: VoiceInference,
                 revoice: Revoice,
                 samples_count: int = 100,
                 ):
        self.target_language = target_language
        self.source = source
        self.train = train
        self.inference = inference
        self.revoice = revoice
        self.samples_count = samples_count

    def __call__(self):
        train_cases = CaseCollection([VoiceTrain.Case(self.train, self.source)])
        train_cases = Chara.call(VoiceTrain.pipeline, "training")(train_cases)
        model = train_cases.successes[0].model

        inference_cases = [VoiceInference.Case(self.inference, model, s) for s in self.target_language.upsampling_dataset_reader()[:self.samples_count]]
        inference_cases = Chara.call(VoiceInference.pipeline, "inference")(CaseCollection(inference_cases))

        revoice_cases = []
        for case in inference_cases.successes:
            rcase = Revoice.Case(case.result, self.revoice, model)
            rcase.text = case.text
            revoice_cases.append(rcase)
        revoice_cases = Chara.call(Revoice.pipeline, "revoice")(CaseCollection(revoice_cases))

        return revoice_cases

















