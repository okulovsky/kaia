import shutil
from chara import Chara
from ..common import CosyRevoice, CosyVoiceTrain, CosyVoiceInference
from ..utilities.sample_translation_pipeline import SampleTranslationPipeline
from chara.common.descriptions import Language
from chara.common.tools.drawing import Drawer, Wav
import os

def translate_samples(
        name: str,
        target_language: str,
        source_language: str = 'en',
        export: list[str] | None = None
    ):
    FOLDER = Chara.Apis.content_folder/'voice_clone'/name

    pipeline = SampleTranslationPipeline(
        Language.from_code(target_language),
        FOLDER/source_language/'source',
        CosyVoiceTrain(),
        CosyVoiceInference(True),
        CosyRevoice()
    )
    Chara.start(FOLDER/target_language/'$sample_translation')
    cases = Chara.call(pipeline)()

    export_folder= FOLDER/target_language/'source'
    os.makedirs(export_folder, exist_ok=True)
    if export is not None:
        for index, file in enumerate(export):
            case = next(c for c in cases.successes if c.result.name == file)
            shutil.copy(case.result, export_folder/f'{index}.wav')
            (export_folder/f'{index}.wav.transcription').write_text(case.text)

    return (
        Drawer(cases.successes, lambda z: Wav(z.result))
        .table(lambda z: z.result.name, lambda z: z.text)
        .to_html()
    )
