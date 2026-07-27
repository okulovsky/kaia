import numpy as np
from ..common import State
from ..common.content_manager import ContentManager
from ..image_service import MediaLibrary
from .narrator import INarrator


class SimpleNarrator(INarrator):
    def __init__(self,
                 content_manager: ContentManager | None = None,
                 randomize: bool = True,
                 ):
        self.content_manager = content_manager
        self.randomize = randomize
        self.characters = self._discover_characters()

    def _discover_characters(self) -> tuple[str, ...]:
        if self.content_manager is None:
            return ()
        records = self.content_manager.match().get_all_acceptable()
        characters = {r.tags.get('character') for r in records if r.tags.get('character') is not None}
        return tuple(sorted(characters))

    def _random_change(self, current, collection: tuple | None) -> str | None:
        if collection is None:
            return None
        others = [c for c in collection if c != current]
        if self.randomize:
            if len(others) == 0:
                return None
            idx = np.random.randint(0, len(others))
            if idx >= len(others):
                idx = len(others) - 1
            return others[idx]
        else:
            return others[0]

    def update_character(self, state: State, character: str | None = None) -> str | None:
        if character is None:
            character = self._random_change(state.character, self.characters)
        if character is not None:
            state.character = character
        return character

    def update_activity(self, state: State) -> list[MediaLibrary.Record]:
        state.activity = None
        if self.content_manager is None or state.character is None:
            return []
        record = (
            self.content_manager.match()
            .strong({'character': state.character, 'special_day': None})
            .find_content()
        )
        if record is None:
            return []
        activity = record.tags.get('activity')
        state.activity = activity
        self.content_manager.feedback(record.path, 'seen')
        siblings = (
            self.content_manager.match()
            .strong({'character': state.character, 'activity': activity, 'special_day': None})
            .get_all_acceptable()
        )
        return [r.original_record for r in siblings]

    def initialize(self, state: State) -> list[MediaLibrary.Record]:
        self.update_character(state)
        return self.update_activity(state)

    def regular_update(self, state: State) -> list[MediaLibrary.Record]:
        return self.update_activity(state)
