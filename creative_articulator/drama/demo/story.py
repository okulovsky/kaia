from typing import Iterable

from chara.common.llm import ILLM

from ..data import Character, Node
from ..driver import IEngine, SequenceEngine
from ..scene import (
    ISceneRules,
    LLMCharacterChooser,
    LLMContinuer,
    LLMQuestionAnswerer,
    SceneEngine,
    SceneSettings,
    SceneShorteningPostprocessor,
    Summarizer,
)
from .characters import get_character
from .scenes import SCENES, DemoScene

INTRO = (
    'The story is set in the village of Prostokvashino, in the middle of winter. In a wooden house at the edge '
    'of it live Matroskin, a talking cat who runs the household and the accounts, and Sharik, a talking dog who '
    'runs everywhere else. Pechkin, the village postman, calls on them far more often than the post requires. '
    'Matroskin and Sharik have quarrelled and are not speaking to each other: they sit in the same room and '
    'each behaves as though the other were not there. '
    'The tone is warm and comic: the bickering is constant, and none of it is ever really cruel.'
)


def build_settings() -> SceneSettings:
    return SceneSettings(
        intro=INTRO,
        desired_user_messages_count_in_scene=8,
        message_length_in_words=30,
        max_sentences_in_summary=3,
    )


def build_scene_engine(llm: ILLM) -> SceneEngine:
    return SceneEngine(
        character_chooser=LLMCharacterChooser(llm),
        question_answerer=LLMQuestionAnswerer(llm),
        continuer=LLMContinuer(llm),
        regular_postprocessor=SceneShorteningPostprocessor(llm),
        final_postprocessor=Summarizer(llm),
    )


def build_story(
        protagonist: Character | str,
        llm: ILLM,
        scenes: Iterable[DemoScene] = SCENES,
        settings: SceneSettings | None = None,
) -> Node:
    if isinstance(protagonist, str):
        protagonist = get_character(protagonist)

    story = Node()
    story[SceneSettings] = settings if settings is not None else build_settings()
    story.attach(SequenceEngine(), custom_type=IEngine)

    for scene in scenes:
        node = Node()
        node[ISceneRules] = scene.build_rules(protagonist)
        node.attach(build_scene_engine(llm), custom_type=IEngine)
        story.append(node)

    return story
