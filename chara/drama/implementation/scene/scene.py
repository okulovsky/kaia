from dataclasses import dataclass, field
from enum import IntEnum
import re

class CharacterPriority(IntEnum):
    Leading = 0
    Supporting = 1
    Mentioned = 2


@dataclass
class Character:
    name: str
    description: str
    priority: CharacterPriority | None = None
    style: str | None = None

class Medium(IntEnum):
    default = 0
    speech = 1
    messenger = 2

@dataclass
class Message:
    name: str
    content: str

    def __str__(self):
        return f'{self.name}: {self.content}'

    @staticmethod
    def parse(s: str):
        try:
            match = re.match('([^:]+):(.*)', s)
            if match is None:
                raise ValueError(f"Bad format\n{s}")
            return Message(match.group(1).strip(), match.group(2).strip())
        except:
            print(s)
            raise

@dataclass
class SceneProgress:
    goal: str | None = None
    progress: float = 0
    goal_check_requested: bool = False
    finalization_requested: bool = False
    length_strict: bool = False

@dataclass
class SceneContext:
    medium: Medium = Medium.speech
    intro: str = ''
    scene_intro: str = ''
    previous_summaries: tuple[str,...] = ()
    intermediate_summaries: tuple[str,...] = ()


@dataclass
class Scene:
    progress: SceneProgress = field(default_factory=SceneProgress)
    context: SceneContext = field(default_factory=SceneContext)
    user_character: Character | None = None
    characters: tuple[Character,...] = ()
    messages: tuple[Message,...] = ()

