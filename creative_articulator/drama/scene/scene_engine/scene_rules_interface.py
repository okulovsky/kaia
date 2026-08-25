from chara.common.llm import QuestionList
from ...data import Node, Message, Character
from .actors import Actors


class ISceneRules:
    def get_actors(self) -> Actors:
        raise NotImplementedError()

    def get_announcements(self, scene: Node) -> list[Message]:
        return []

    def get_hints(self, scene: Node, character: Character) -> list[str]:
        return []

    def is_custom_scene_ending(self, scene: Node) -> bool|None:
        return None

    def get_ending_questions(self, scene: Node) -> QuestionList:
        raise NotImplementedError()

    def resolve_ending_questions(self, answers: dict) -> bool:
        raise NotImplementedError()
