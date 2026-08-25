from ...data import Node, Character
from ..scene_engine.interfaces import ICharacterChooser
from chara.common.llm import ILLM
from pathlib import Path
from .random_character_chooser import RandomCharacterChooser

class LLMCharacterChooser(ICharacterChooser):
    def __init__(self, source: ILLM[Node, Character]):
        request = (source
                   .default()
                   .template(Path(__file__).parent / 'llm_character_chooser.jinja')
                   .to_request())
        self.request = request.edit().parse(self._parse).to_request()

    def _parse(self, current: Node, output: str) -> Character:
        name_to_character = self.get_name_to_character(current)
        name = output.strip()
        if name in name_to_character:
            return name_to_character[name]
        # The LLM named nobody we know, so fall back. This only runs when no one has
        # answered yet, which is the only situation choose_next_speaker asks the LLM in.
        return RandomCharacterChooser().choose_next_speaker(current, 0)

    def choose_next_speaker(self, current: Node, responses_count: int) -> Character|None:
        if responses_count > 0:
            return None
        return self.request.execute(current)
