from chara import Chara, CaseCollection, BrainBoxCasePipeline, AnnotationPipeline, AudioLabelAnnotator, \
    LabelAnnotatorSettings, SimpleTaskPlanner
from chara.common.descriptions import Language
from chara.common.tools import Wav
from pathlib import Path
from typing import Callable

from chara.voice_clone import VoiceTrain, VoiceInference, Revoice
from chara.voice_clone.common.revoice import RevoiceCase


class _DurationLimitedTaskPlanner(SimpleTaskPlanner[RevoiceCase]):
    def __init__(self, durations: dict[str, float], required_duration_sec: float, accepted_label: str):
        super().__init__()
        self.durations = durations
        self.required_duration_sec = required_duration_sec
        self.accepted_label = accepted_label

    def get_next(self) -> str | None:
        collected = sum(
            self.durations[id]
            for id, status in self.cache.get_annotation_status().items()
            if status.value == self.accepted_label
        )
        if collected >= self.required_duration_sec:
            return None
        return super().get_next()


class SampleTranslationPipeline:
    def __init__(self,
                 target_language: Language,
                 source: Path,
                 train: VoiceTrain,
                 inference: VoiceInference,
                 revoice: Revoice,
                 samples_count: int = 100,
                 required_samples: list[str]|None = None,
                 required_duration_sec: float = 30,
                 mock_annotation: Callable[[RevoiceCase], str]|None = None,
                 ):
        self.target_language = target_language
        self.source = source
        self.train = train
        self.inference = inference
        self.revoice = revoice
        self.samples_count = samples_count
        self.required_samples = required_samples
        self.required_duration_sec = required_duration_sec
        self.mock_annotation = mock_annotation

    def __call__(self):
        train_cases = CaseCollection([VoiceTrain.Case(self.train, self.source)])
        train_cases = Chara.call(VoiceTrain.pipeline, "training")(train_cases)
        model = train_cases.successes[0].model

        samples = self.target_language.upsampling_dataset_reader()[:self.samples_count]
        if self.required_samples is not None:
            samples = self.required_samples + samples

        inference_cases = [VoiceInference.Case(self.inference, model, s) for s in samples]
        inference_cases = Chara.call(VoiceInference.pipeline, "inference")(CaseCollection(inference_cases))

        revoice_cases = []
        for case in inference_cases.successes:
            rcase = Revoice.Case(case.result, self.revoice, model)
            rcase.text = case.text
            revoice_cases.append(rcase)
        revoice_cases = Chara.call(Revoice.pipeline, "revoice")(CaseCollection(revoice_cases))

        return self._review(revoice_cases)

    def _review(self, cases: CaseCollection[RevoiceCase]) -> CaseCollection[RevoiceCase]:
        durations = {c.get_id(): Wav(c.result).to_editable().duration_sec for c in cases.successes}

        settings = LabelAnnotatorSettings(('YES', 'NO'))
        planner = _DurationLimitedTaskPlanner(durations, self.required_duration_sec, 'YES')
        annotator = AudioLabelAnnotator(lambda case: case.result, settings, planner, mock_annotation=self.mock_annotation)
        review_pipeline = AnnotationPipeline(annotator, 'annotation')
        reviewed_cases = Chara.call(review_pipeline.__call__, "review")(cases)

        good_cases = [c for c in reviewed_cases.successes if c.annotation == 'YES']
        selected = []
        total = 0.0
        for case in good_cases:
            if total >= self.required_duration_sec:
                break
            selected.append(case)
            total += durations[case.get_id()]
        if total >= self.required_duration_sec:
            selected = selected[:-1]

        return CaseCollection(selected)
