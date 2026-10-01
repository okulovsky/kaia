import numpy as np
from ..common import State
from ..common.content import ContentFinder, IRecord, IFeedbackStorage, InMemoryFeedbackStorage
from .narrator import INarrator


class SimpleNarrator(INarrator):
    def __init__(self,
                 records: list[IRecord] | None = None,
                 feedback_storage: IFeedbackStorage | None = None,
                 finder: ContentFinder | None = None,
                 randomize: bool = True,
                 ):
        self.records = records
        self.feedback_storage = feedback_storage if feedback_storage is not None else InMemoryFeedbackStorage()
        self.finder = finder if finder is not None else ContentFinder()
        self.randomize = randomize
        self.characters = self._discover_characters()

    def _discover_characters(self) -> tuple[str, ...]:
        if self.records is None:
            return ()
        characters = {
            r.get_tags().get('character') for r in self.records
            if r.get_tags().get('character') is not None
        }
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

    def update_activity(self, state: State) -> list[IRecord]:
        state.activity = None
        if self.records is None or state.character is None:
            return []
        feedback = self.feedback_storage.load()
        record = self.finder.find(
            self.records,
            feedback,
            strong={'character': state.character, 'special_day': None},
        )
        if record is None:
            return []
        activity = record.get_tags().get('activity')
        state.activity = activity
        self.feedback_storage.append(record.get_id(), {'seen': 1})
        return self.finder.select(
            self.records,
            strong={'character': state.character, 'activity': activity, 'special_day': None},
        )

    def initialize(self, state: State) -> list[IRecord]:
        self.update_character(state)
        return self.update_activity(state)

    def regular_update(self, state: State) -> list[IRecord]:
        return self.update_activity(state)
