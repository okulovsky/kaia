from dataclasses import dataclass
from ...data import Message, Node, Character
from ...driver import SceneState
from chara.common.llm import QuestionList
from .scene_rules_interface import ISceneRules
from .actors import Actors
from .scene_settings import SceneSettings

@dataclass
class SceneStageHint:
    character_hints: dict[str, list[str]]
    announcement: str|Message|list[str|Message]|None = None
    progress: float | None = None

@dataclass
class SceneHint:
    stages: list[SceneStageHint]

    def __post_init__(self):
        for index, stage in enumerate(self.stages):
            if stage.progress is None:
                stage.progress = index/(len(self.stages)-1)


class SceneRules(ISceneRules):
    def __init__(self, actors: Actors, hints: SceneHint, ending_questions: QuestionList) -> None:
        self.actors = actors
        self.hints = hints
        self.ending_questions = ending_questions

        is_stage_progress_none = set(s.progress is None for s in self.hints.stages)
        if len(is_stage_progress_none) != 1:
            raise ValueError("All the scenes must have the progress, or none of them")
        if True in is_stage_progress_none:
            for index, stage in enumerate(self.hints.stages):
                stage.progress = index/(len(self.hints.stages)-1)

    def get_actors(self) -> Actors:
        return self.actors

    def get_progresses(self, current: Node):
        state: SceneState = current[SceneState]
        total = len([m for m in state.messages if m.speaker == self.actors.protagonist.name])
        maximum = current.root[SceneSettings].desired_user_messages_count_in_scene
        return (total-1)/maximum, total/maximum

    def get_stage(self, current: Node, first_time_only: bool) -> SceneStageHint|None:
        previous_progress, current_progress = self.get_progresses(current)
        current_stage = self.hints.stages[0]
        for stage in self.hints.stages:
            if stage.progress <= current_progress:
                current_stage = stage
            else:
                break
        if first_time_only:
            if current_stage.progress > previous_progress:
                return current_stage
            return None
        return current_stage

    def get_announcements(self, scene: Node) -> list[Message]:
        stage = self.get_stage(scene, True)
        if stage is None:
            return []
        if stage.announcement is None:
            return []
        if isinstance(stage.announcement, Message):
            return [stage.announcement]
        if isinstance(stage.announcement, str):
            return [Message.from_text(stage.announcement)]
        result = []
        for item in stage.announcement:
            if isinstance(item, Message):
                result.append(item)
            else:
                result.append(Message.from_text(item))
        return result

    def get_hints(self, scene: Node, character: Character) -> list[str]:
        stage = self.get_stage(scene, False)
        if stage is None:
            return []
        if character.name not in stage.character_hints:
            return []
        return stage.character_hints[character.name]

    def get_ending_questions(self, scene: Node) -> QuestionList:
        return self.ending_questions

    def resolve_ending_questions(self, answers: dict) -> bool:
        return all(answers.values())








