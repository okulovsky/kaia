from ...data import IDiff, Message, Node
from .story_state import StoryState
from .scene_state import SceneState
from dataclasses import dataclass
from copy import deepcopy

@dataclass
class AddMessageDiff(IDiff):
    message: Message

    def __post_init__(self):
        self.message = deepcopy(self.message)

    def apply(self, root: Node):
        current = root[StoryState].current_node
        current[SceneState].messages.append(self.message)
