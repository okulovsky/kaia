from dataclasses import dataclass
from abc import ABC, abstractmethod
from ...data import Node, Character, Message, IDiff
from ...driver import SceneState
from .scene_rules_interface import ISceneRules
from typing import Any, Iterable
from chara.common.llm import QuestionList

class ICharacterChooser(ABC):
    @abstractmethod
    def choose_next_speaker(self, current: Node, responses_count: int) -> Character|None:
        pass

    def compute_current_counts(self, current: Node):
        actors = current[ISceneRules].get_actors()
        state = current[SceneState]
        characters = actors.characters

        counts = {c.name: 0 for c in characters.many}
        for message in reversed(state.messages):
            if message.from_user:
                break
            if message.speaker in counts:
                counts[message.speaker] += 1
        return counts

    def get_name_to_character(self, current: Node) -> dict[str, Character]:
        actors = current[ISceneRules].get_actors()
        return {c.name: c for c in actors.characters.many}



class IQuestionAnswerer(ABC):
    @abstractmethod
    def answer(self, current: Node, questions: QuestionList) -> dict:
        pass

@dataclass
class ContinuationCase:
    scene: Node
    character: Character
    hints: list[str]

class IContinuer(ABC):
    @abstractmethod
    def continue_scene(self, case: ContinuationCase) -> Message:
        pass

class IScenePostprocessor(ABC):
    def postprocess(self, current: Node) -> Iterable[IDiff]:
        pass