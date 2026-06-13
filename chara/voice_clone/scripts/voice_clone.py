from chara.common import Language, Chara
from ..common import CosyVoiceTrain, CosyVoiceInference
from ..distillation import DistillationPipeline, DistillationSettings, LanguageSettings
from brainbox.deciders import PiperTraining

def clone_voice(name: str, language: str):
    settings = DistillationSettings(
        LanguageSettings.from_language(Language.from_code(language)),
        PiperTraining.TrainingParameters(
            epochs=200,
            checkpoint_epochs=10,
            keep_intermediate=True
        ),
        CosyVoiceTrain(),
        CosyVoiceInference(False),
        2000,
        max_upsampling_attempts=3,
    )
    src = Chara.Apis.content_folder / f'voice_clone/{name}/{language}/source'
    target = Chara.Apis.content_folder / f'voice_clone/{name}/{language}/$training'
    Chara.start(target)
    pipe = DistillationPipeline(settings)
    Chara.call(pipe)(f'{name}_{language}', src)