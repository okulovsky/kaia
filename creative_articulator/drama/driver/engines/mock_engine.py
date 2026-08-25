import re
import time

from eaglesong import Listen
from .engine import Iterable, IEngine, EngineOutput
from ...data import Node, Message
from ..basic_diffs import SceneState, Listen, PopDiff


MANY_PATTERN = re.compile(r'MANY\((\d+(?:\.\d+)?)\)')
POP = re.compile(r'POP')


class MockEngine(IEngine):
    def __init__(self,
                 buffer_message: int = 20,
                 time_to_message_in_seconds: float = 0,
                 character_name: str = 'Alice',
                 ):
        self.buffer_message = buffer_message
        self.time_to_message_in_seconds = time_to_message_in_seconds
        self.character_name = character_name

    def generate(self, current: Node) -> Iterable[EngineOutput]:
        state = current[SceneState]
        if len(state.messages) == 0:
            yield Message.from_text("* Opening *")
            for i in range(self.buffer_message):
                yield Message.from_text(f"Buffer message #{i}", self.character_name)
        else:
            last_message = state.messages[-1]
            yield Message.from_text(f"Reply to: "+last_message.__str__(), self.character_name)
            match = MANY_PATTERN.search(last_message.__str__())
            if match:
                for i in range(int(match.group(1))-1):
                    time.sleep(self.time_to_message_in_seconds)
                    yield Message.from_text(f"Reply #{i+2} to: "+last_message.__str__(), self.character_name)
            if not POP.search(last_message.__str__()):
                yield Listen()
            else:
                yield PopDiff()


