from ...data import Node, IDiff, Message
from copy import deepcopy
from ..basic_diffs import StoryState, Listen, IFlowBreakingDiff, AddMessageDiff
from .engine import IEngine
from typing import Iterable

class StoryDriver:
    def __init__(self, story: Node) -> None:
        self.story_backup = deepcopy(story)
        self.story: Node | None = None

    def reset(self, diffs: list[IDiff]|None = None):
        self.story = deepcopy(self.story_backup)
        self.story[StoryState].current_node = self.story
        self.story[StoryState].finalized = False
        if diffs is not None:
            for diff in diffs:
                diff.apply(self.story)


    def generate(self) -> Iterable[IDiff]:
        while True:
            current = self.story[StoryState].current_node
            if current is None:
                if self.story[StoryState].finalized:
                    break
                raise ValueError("current_node is None, but the story is not finalized: the driver wasn't initialized (call reset() first)")
            stop = False
            for output in current[IEngine].generate(current):
                if isinstance(output, Listen):
                    stop = True
                    break
                if isinstance(output, Message):
                    output = AddMessageDiff(output)
                if not isinstance(output, IDiff):
                    raise ValueError(f"output expected to be IDiff, but was {output}")
                yield output
                if isinstance(output, IFlowBreakingDiff):
                    break
            if stop:
                break

    def generate_and_apply(self) -> list[IDiff]:
        result = []
        for diff in self.generate():
            diff.apply(self.story)
            result.append(diff)
        return result