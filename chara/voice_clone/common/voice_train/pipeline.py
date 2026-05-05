from __future__ import annotations
import os
import shutil
from chara.common import Chara, CaseCollection, brainbox_pipeline
from .small_classes import VoiceTrainCase, VoiceTrainMetadata
from chara.common.tools import Wav
from typing import TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .voice_train import VoiceTrain

def _read_metadata(path, trainer: VoiceTrain) -> dict[str,str]:
    return {
        extension: Path(str(path) + '.' + extension).read_text()
        for extension in trainer.get_metadata_extensions()
    }

def _write_metadata(path, metadata: dict[str,str]) -> None:
    for extension, data in metadata.items():
        Path(str(path) + '.' + extension).write_text(data)

def _recode_in_proper_format(cases: CaseCollection[VoiceTrainCase]) -> CaseCollection[VoiceTrainCase]:
    for index, case in enumerate(cases.cases):
        if case.source.is_file():
            files = [case.source]
        elif case.source.is_dir():
            files = list(case.source.iterdir())
        else:
            raise ValueError(f"{case.source} is not a file or a directory")

        folder = Chara.current.folder/f"recode_{index}"
        samples = []
        os.makedirs(folder, exist_ok=True)
        for file in files:
            if file.name.endswith('.wav') or file.name.endswith('.mp3') or file.name.endswith('.aac'):
                name = case.trainer.recode_in_proper_format(file, folder)
                samples.append(folder/name)
                _write_metadata(folder/name, _read_metadata(file, case.trainer))

        case.recoded_samples = samples
    return CaseCollection(cases)


def _create_train_samples(cases: CaseCollection[VoiceTrainCase]) -> CaseCollection[VoiceTrainCase]:
    for index, case in enumerate(cases.successes):
        folder = Chara.current.folder/f"prepare_{index}"
        os.makedirs(folder, exist_ok=True)
        ex = case.trainer.requires_train_single_file_with_extension()
        if ex is not None and len(case.recoded_samples) > 1:
            paths = []
            metadatas = []
            for path in case.recoded_samples:
                paths.append(path)
                metadatas.append(_read_metadata(path, case.trainer))

            target_path = folder / f'sample.{ex}'
            Wav.concat_with_ffmpeg(
                paths,
                target_path
            )
            aggregated_metadatas = case.trainer.aggregate_metadata(metadatas)
            _write_metadata(target_path, aggregated_metadatas)
            case.train_samples = [target_path]
        else:
            for file in case.recoded_samples:
                shutil.copy(file, folder / file.name)
                _write_metadata(folder / file.name, _read_metadata(file, case.trainer))
            case.train_samples = [folder / f.name for f in case.recoded_samples]
    return CaseCollection(cases)

def _prepare_all(cases: CaseCollection[VoiceTrainCase]) -> CaseCollection[VoiceTrainCase]:
    cases = Chara.call(_recode_in_proper_format)(cases).raise_if_any_error()
    cases = Chara.call(_create_train_samples)(cases).raise_if_any_error().cases
    for case in cases:
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