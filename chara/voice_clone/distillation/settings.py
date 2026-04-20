from dataclasses import dataclass
from typing import Callable
from chara.common.descriptions import Language
from brainbox.deciders import PiperTraining
from ..upsampling import UpsamplingSettings
from ..common import VoiceTrain, VoiceInference

@dataclass
class LanguageSettings:
    language: Language
    verifier_prefix_max_skip: int
    verifier_suffix_max_skip: int
    verifier_max_allowed_distance: int
    verifier_additional_transform: Callable[[str], str] | None
    step_prefix: str
    step_suffix: str
    piper_base_model: str
    voiceover_example: str

    @staticmethod
    def from_language(language: Language) -> 'LanguageSettings':
        if language.code == 'en':
            return LanguageSettings(
                language=language,
                verifier_prefix_max_skip=4,
                verifier_suffix_max_skip=4,
                verifier_max_allowed_distance=2,
                verifier_additional_transform=None,
                step_prefix="The beginning. ",
                step_suffix=" The end.",
                piper_base_model=PiperTraining.Models.lessac,
                voiceover_example="Pete bought a big bag of cheap red apples and fresh fish for Sue. Those thieves thought that this weather was rather unusual. A joyful wizard quickly mixed beige liquids in huge jars."
            )

        if language.code == 'ru':
            return LanguageSettings(
                language=language,
                verifier_prefix_max_skip=4,
                verifier_suffix_max_skip=4,
                verifier_max_allowed_distance=2,
                verifier_additional_transform=lambda z: z.replace('ё', 'e'),
                step_prefix="Я начинаю. ",
                step_suffix=" Я закончил.",
                piper_base_model=PiperTraining.Models.denis,
                voiceover_example="Шустрый ёж съел мягкий хлеб, выпил чаю и лёг спать. Вьюга бьёт по съёмным крышам, гулко звенят цепи. Фальшивый джаз гремел, хриплый вокал дрожал."
            )

        if language.code == 'de':
            return LanguageSettings(
                language=language,
                verifier_prefix_max_skip=4,
                verifier_suffix_max_skip=4,
                verifier_max_allowed_distance=2,
                verifier_additional_transform=lambda z: z.replace('ß', 'ss'),
                step_prefix="Der Beginn. ",
                step_suffix=" Das Ende.",
                piper_base_model=PiperTraining.Models.thorsten,
                voiceover_example="Fünf große Boxkämpfer jagen zwölf quirlige Zwerge. Der schlaue Junge hörte plötzlich seltsame Geräusche. Zwischen zwei Bächen quaken fröhliche Frösche laut."
            )

        raise ValueError(f"No distillation settings for language '{language.name}'")


@dataclass
class DistillationSettings:
    language_settings: LanguageSettings
    upsampling_settings: UpsamplingSettings
    training_settings: PiperTraining.TrainingParameters
    train: VoiceTrain
    inference: VoiceInference

