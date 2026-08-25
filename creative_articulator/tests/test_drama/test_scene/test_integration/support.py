from creative_articulator.drama.data import Node, Character, CharacterReference, Message
from creative_articulator.drama.driver import IEngine, SceneState, StoryDriver
from creative_articulator.drama.scene import Actors, SceneSettings
from creative_articulator.drama.scene.scene_engine import SceneEngine, SceneRules, ISceneRules
from creative_articulator.drama.scene.scene_engine.interfaces import IScenePostprocessor
from creative_articulator.drama.scenario.plan import Persuasion
from creative_articulator.drama.scene.implementations import RandomCharacterChooser, LLMContinuer, LLMQuestionAnswerer
from chara.common.llm import LLMSetup, MockLLMEngine, Question, QuestionList

PROTAGONIST_NAME = 'Alex'
NPC_NAME = 'Bob'
GOAL = 'convince Bob to leave the house'


def character(name: str) -> Character:
    return Character(name, Character.Gender.Neutral, f'{name} description')


def mock_setup(*replies: str) -> LLMSetup:
    return LLMSetup(MockLLMEngine(*replies), 'mock-model')


def build_driver(
        llm: LLMSetup,
        messages: list[Message],
        settings: SceneSettings|None = None,
        regular_postprocessor: IScenePostprocessor|None = None,
        final_postprocessor: IScenePostprocessor|None = None,
) -> StoryDriver:
    """
    Builds a single root Node with a SceneEngine (using Persuasion rules and
    MockLLMEngine-backed implementations), pre-populated with `messages`, and wraps
    it into a StoryDriver ready for `reset()` + `generate_and_apply()`.
    """
    protagonist = character(PROTAGONIST_NAME)
    npc = character(NPC_NAME)
    target = CharacterReference(npc)
    actors = Actors(CharacterReference(protagonist), target)

    plan = Persuasion(target, GOAL).describe(actors)
    ending_questions = QuestionList([
        Question(t.name + '_completed', f'Have {t.name} done this: `{GOAL}`?', bool)
        for t in target
    ])

    story = Node()
    story[SceneSettings] = settings if settings is not None else SceneSettings()
    story[SceneState].messages.extend(messages)
    story[ISceneRules] = SceneRules(actors, plan.hint, ending_questions)

    engine = SceneEngine(
        character_chooser=RandomCharacterChooser(),
        question_answerer=LLMQuestionAnswerer(llm),
        continuer=LLMContinuer(llm),
        regular_postprocessor=regular_postprocessor,
        final_postprocessor=final_postprocessor,
    )
    story.attach(engine, custom_type=IEngine)

    return StoryDriver(story)


def completed_question_answer(is_completed: bool) -> str:
    return '{"' + NPC_NAME + '_completed": ' + ('true' if is_completed else 'false') + '}'
