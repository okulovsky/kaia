from dataclasses import dataclass
from typing import Iterable

from ...data import IDiff, Message, Node
from ...driver import SceneState, StoryState
from chara.common.llm import ILLM
from ..scene_engine import IScenePostprocessor, SceneSettings
from pathlib import Path

@dataclass
class SceneShorteningDiff(IDiff):
    shortening_index: int
    shortening: str

    def apply(self, root: Node):
        state: SceneState = root[StoryState].current_node[SceneState]
        state.shortening = self.shortening
        state.shortening_index = self.shortening_index


@dataclass
class SceneShorteningCase:
    to_shorten: list[Message]

class SceneShorteningPostprocessor(IScenePostprocessor):
    def __init__(self, source: ILLM[SceneShorteningCase, str]):
        request = (source
                   .default()
                   .template(Path(__file__).parent / 'scene_shortening_postprocessor.jinja')
                   .to_request())
        self.request = request.edit().parse(lambda case, output: output.strip()).to_request()

    def postprocess(self, current: Node) -> Iterable[IDiff]:
        settings = current.root[SceneSettings]
        state = current[SceneState]
        if len(state.messages) - state.shortening_index > settings.min_messages_for_shortening:
            to_shorten = current[SceneState].messages[:-settings.min_messages_after_shortening]
            case = SceneShorteningCase(to_shorten)
            summary = self.request.execute(case)
            yield SceneShorteningDiff(len(to_shorten), summary)

