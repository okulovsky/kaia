from pathlib import Path
from typing import Iterable
from chara.common.llm import ILLM
from ..scene_engine.interfaces import IScenePostprocessor
from dataclasses import dataclass
from ...data import IDiff, Node
from ...driver import StoryState, SceneState

@dataclass
class SceneSummaryDiff(IDiff):
    summary: str

    def apply(self, root: Node):
        root[StoryState].current_node[SceneState].summary = self.summary


class Summarizer(IScenePostprocessor):
    def __init__(self, source: ILLM[Node, str]):
        request = source.default().template(Path(__file__).parent / 'summarizer.jinja').to_request()
        self.request = request.edit().parse(lambda case, output: output.strip()).to_request()

    def postprocess(self, current: Node) -> Iterable[IDiff]:
        yield SceneSummaryDiff(self.request.execute(current))
