import random

from ...data import Node, Character
from ...driver import SceneState
from ..scene_engine.interfaces import ICharacterChooser


class RandomCharacterChooser(ICharacterChooser):
    def choose_next_speaker(self, current: Node, responses_count: int) -> Character|None:
        if responses_count > 0:
            return None
        counts = self.compute_current_counts(current)
        minimal = min(counts.values())
        name_to_character = self.get_name_to_character(current)
        candidates = [name_to_character[name] for name, count in counts.items() if count == minimal]
        return random.choice(candidates)
