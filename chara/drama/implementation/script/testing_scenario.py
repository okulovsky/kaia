from typing import Iterable
from ..scene import ISceneProcessor, SceneProcessorResult, Scene, Message
from .linear_script import LinearScript
from .past_scene import PastPlay, PastScene


class FakeSceneProcessor(ISceneProcessor):
    def __init__(self, reply: SceneProcessorResult):
        self.reply = reply

    def process(self, scene: Scene) -> SceneProcessorResult:
        return self.reply


class TestingScenario:
    def __init__(self, replies: Iterable[SceneProcessorResult]):
        self.replies = list(replies)
        self.past_play = None
        self.linear_scenario = None


    def run(self, linear_script: LinearScript):
        messages = tuple()
        for i, reply in enumerate(self.replies):
            self.past_play = PastPlay.from_messages(messages)
            messages+=(Message(linear_script.user_character, f"input #{i+1}"))
            scene = linear_script.generate_scene(self.past_play)
            result = FakeSceneProcessor(reply).process(scene)
            messages+=result.next_messages
            tags = result.get_tags()
            if tags is not None:
                messages+=(tags,)
        return PastPlay.from_messages(messages)


