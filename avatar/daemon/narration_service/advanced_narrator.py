from collections import OrderedDict
from datetime import datetime
from typing import Callable
from ..common import State
from ..common.content import ContentFinder, IRecord, IFeedbackStorage
from .simple_narrator import SimpleNarrator
from .state_field_setter import IStateFieldSetter


class AdvancedNarrator(SimpleNarrator):
    def __init__(self,
                 records: list[IRecord] | None,
                 feedback_storage: IFeedbackStorage | None,
                 state_field_setters: list[IStateFieldSetter],
                 finder: ContentFinder | None = None,
                 fuzzy_tag_order: tuple[str, ...] = ('time_of_day', 'season', 'good_weather'),
                 randomize: bool = True,
                 datetime_factory: Callable[[], datetime] = datetime.now,
                 ):
        super().__init__(records, feedback_storage, finder, randomize)
        self.state_field_setters = state_field_setters
        self.fuzzy_tag_order = fuzzy_tag_order
        self.datetime_factory = datetime_factory

    def _update_tags(self, state: State) -> None:
        now = self.datetime_factory()
        for setter in self.state_field_setters:
            setter.update(state, now)

    def update_activity(self, state: State) -> list[IRecord]:
        state.activity = None
        if self.records is None or state.character is None:
            return []
        fuzzy_tags = OrderedDict(
            (tag, getattr(state, tag))
            for tag in self.fuzzy_tag_order
            if getattr(state, tag, None) is not None
        )
        feedback = self.feedback_storage.load()
        pool = self.finder.select(
            self.records,
            strong={'character': state.character, 'special_day': state.special_day},
            fuzzy=fuzzy_tags,
        )
        record = self.finder.choose(pool, feedback)
        if record is None:
            return []
        activity = record.get_tags().get('activity')
        state.activity = activity
        self.feedback_storage.append(record.get_id(), {'seen': 1})
        return [r for r in pool if r.get_tags().get('activity') == activity]

    def initialize(self, state: State) -> list[IRecord]:
        self._update_tags(state)
        self.update_character(state)
        return self.update_activity(state)

    def regular_update(self, state: State) -> list[IRecord]:
        self._update_tags(state)
        if state.special_day is not None:
            self.update_character(state)
        return self.update_activity(state)
