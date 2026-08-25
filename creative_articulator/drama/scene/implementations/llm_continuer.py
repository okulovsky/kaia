import random
import re
from pathlib import Path
from chara.common.llm import ILLM
from ...data import Message
from ..scene_engine.interfaces import IContinuer, ContinuationCase


class LLMContinuer(IContinuer):
    def __init__(self, source: ILLM[ContinuationCase, Message]):
        request = (source
                   .default()
                   .template(Path(__file__).parent / 'llm_continuer.jinja')
                   .to_request())
        self.request = request.edit().parse(self._parse).to_request()

    def _parse(self, case: ContinuationCase, output: str) -> Message:
        candidates = re.findall(r'^\s*\d+[.)]\s*(.+)$', output, re.MULTILINE)
        if not candidates:
            candidates = [output]
        choice = random.choice(candidates)
        if ':' in choice and choice.index(':') < 10:
            choice = choice[choice.index(':')+1:]
        return Message(Message.Content.parse(choice.strip()), case.character.name, False)

    def continue_scene(self, case: ContinuationCase) -> Message:
        return self.request.execute(case)
