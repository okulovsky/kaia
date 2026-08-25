from ...driver import IEngine, EngineOutput, SceneState, StoryState, Listen, PopDiff, AddMessageDiff
from ...data import Node, Message
from .scene_settings import SceneSettings
from .interfaces import IContinuer, ICharacterChooser, IQuestionAnswerer, ContinuationCase, IScenePostprocessor
from typing import Iterable
from .scene_rules_interface import ISceneRules
from .elaborator import IElaborator


class SceneEngine(IEngine):
    def __init__(self,
                 character_chooser: ICharacterChooser,
                 question_answerer: IQuestionAnswerer,
                 continuer: IContinuer,
                 regular_postprocessor: IScenePostprocessor|None = None,
                 final_postprocessor: IScenePostprocessor|None = None,
                 elaborator: IElaborator|None = None
                 ):
        self.character_chooser = character_chooser
        self.question_answerer = question_answerer
        self.continuer = continuer
        self.regular_postprocessor = regular_postprocessor
        self.final_postprocessor = final_postprocessor
        self.elaborator = elaborator

    @staticmethod
    def scene_engine_debug_run(engine: 'SceneEngine', current: Node) -> list[Message]:
        current.root[StoryState].current_node = current
        limit = 2 * current.root[SceneSettings].desired_user_messages_count_in_scene
        messages: list[Message] = []
        finished = False

        while not finished and len(messages) < limit:
            protagonist_message = engine.next_protagonist_message(current)
            AddMessageDiff(protagonist_message).apply(current.root)
            messages.append(protagonist_message)

            for output in engine.generate(current):
                if isinstance(output, Listen):
                    continue
                if isinstance(output, Message):
                    messages.append(output)
                    output = AddMessageDiff(output)
                output.apply(current.root)
                if isinstance(output, PopDiff):
                    finished = True

        return messages

    def next_protagonist_message(self, current: Node) -> Message:
        current.ensure(SceneState)
        rules = current[ISceneRules]
        protagonist = rules.get_actors().protagonist.single
        hints = rules.get_hints(current, protagonist)
        return self.continuer.continue_scene(ContinuationCase(current, protagonist, hints))

    def generate(self, current: Node) -> Iterable[EngineOutput]:
        state = current[SceneState]

        rules = current[ISceneRules]

        if len(state.messages) == 0:
            if self.elaborator is not None:
                yield from self.elaborator.elaborate(current)
            actors = rules.get_actors()
            if actors.opening is not None:
                yield Message.from_text(actors.opening)

        yield from rules.get_announcements(current)

        responses_count = 0
        while True:
            character = self.character_chooser.choose_next_speaker(current, responses_count)
            if character is None:
                break
            responses_count += 1
            hints = rules.get_hints(current, character)
            yield self.continuer.continue_scene(ContinuationCase(current, character, hints))

        ending = rules.is_custom_scene_ending(current)
        if ending is None:
            questions = rules.get_ending_questions(current)
            answers = self.question_answerer.answer(current, questions)
            ending = rules.resolve_ending_questions(answers)

        if not ending:
            if self.regular_postprocessor is not None:
                yield from self.regular_postprocessor.postprocess(current)
            yield Listen()
        else:
            if self.final_postprocessor is not None:
                yield from self.final_postprocessor.postprocess(current)
            yield PopDiff()

