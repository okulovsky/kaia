import shutil
from chara import Chara
from ..common import CosyRevoice, CosyVoiceTrain, CosyVoiceInference
from ..utilities.sample_translation_pipeline import SampleTranslationPipeline
from chara.common.descriptions import Language
import os

def translate_samples(
        name: str,
        target_language: str,
        source_language: str = 'en',
        samples_count: int = 100,
        required_sentences: list[str]|None = None
    ):
    FOLDER = Chara.Apis.content_folder/'voice_clone'/name

    pipeline = SampleTranslationPipeline(
        Language.from_code(target_language),
        FOLDER/source_language/'source',
        CosyVoiceTrain(),
        CosyVoiceInference(True),
        CosyRevoice(),
        samples_count=samples_count,
        required_samples=required_sentences
    )
    Chara.start(FOLDER/target_language/'$sample_translation')
    cases = Chara.call(pipeline)()

    export_folder= FOLDER/target_language/'source'
    os.makedirs(export_folder, exist_ok=True)
    for index, case in enumerate(cases.successes):
        shutil.copy(case.result, export_folder/f'{index}.wav')
        (export_folder/f'{index}.wav.transcription').write_text(case.text)
