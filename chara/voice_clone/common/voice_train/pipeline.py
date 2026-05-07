from __future__ import annotations
from chara.common import Chara, CaseCollection, brainbox_pipeline
from .small_classes import VoiceTrainCase, VoiceTrainMetadata
from typing import TYPE_CHECKING
from ._utils import _recode_in_proper_format, _create_train_samples, _read_metadata, _adjust_level

if TYPE_CHECKING:
    from .voice_train import VoiceTrain



def _prepare_all(cases: CaseCollection[VoiceTrainCase]) -> CaseCollection[VoiceTrainCase]:
    cases = Chara.call(_recode_in_proper_format)(cases).raise_if_any_error()
    cases = Chara.call(_create_train_samples)(cases).raise_if_any_error()
    cases = Chara.call(_adjust_level)(cases).raise_if_any_error()
    for case in cases.successes:
        case.task, case.model = case.trainer.create_train_task_and_reference(
            case.train_samples,
            [_read_metadata(f, case.trainer) for f in case.train_samples],
            VoiceTrainMetadata(original_samples_path=case.source)
        )
    return CaseCollection(cases)

def pipeline(cases: CaseCollection[VoiceTrainCase]) -> CaseCollection[VoiceTrainCase]:
    cases = Chara.call(_prepare_all)(cases).raise_if_any_error().successes
    result = Chara.call(brainbox_pipeline)([c.task for c in cases]).read_all().to_list()
    for case, r in zip(cases, result):
        if r.error is not None:
            case.error = r.error
    return CaseCollection(cases)