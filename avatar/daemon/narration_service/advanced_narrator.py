from collections import OrderedDict
from datetime import datetime
from typing import Callable
from ..common import State
from ..common.content_manager import ContentManager
from ..image_service import MediaLibrary
from .simple_narrator import SimpleNarrator
from .state_field_setter import IStateFieldSetter


class AdvancedNarrator(SimpleNarrator):
    def __init__(self,
                 content_manager: ContentManager,
                 state_field_setters: list[IStateFieldSetter],
                 fuzzy_tag_order: tuple[str, ...] = ('time_of_day', 'season', 'weather'),
                 randomize: bool = True,
                 datetime_factory: Callable[[], datetime] = datetime.now,
                 ):
        super().__init__(content_manager, randomize)
        self.state_field_setters = state_field_setters
        self.fuzzy_tag_order = fuzzy_tag_order
        self.datetime_factory = datetime_factory

    def _update_tags(self, state: State) -> None:
        now = self.datetime_factory()
        for setter in self.state_field_setters:
            setter.update(state, now)

    def update_activity(self, state: State) -> list[MediaLibrary.Record]:
        state.activity = None
        if self.content_manager is None or state.character is None:
            return []
        fuzzy_tags = OrderedDict(
            (tag, getattr(state, tag))
            for tag in self.fuzzy_tag_order
            if getattr(state, tag, None) is not None
        )
        record, pool = (
            self.content_manager.match()
            .strong({'character': state.character, 'special_day': state.special_day})
            .fuzzy(fuzzy_tags)
            .find_content_with_pool()
        )
        if record is None:
            return []
        activity = record.tags.get('activity')
        state.activity = activity
        self.content_manager.feedback(record.path, 'seen')
        siblings = [r for r in pool if r.tags.get('activity') == activity]
        return [r.original_record for r in siblings]

    def initialize(self, state: State) -> list[MediaLibrary.Record]:
        self._update_tags(state)
        self.update_character(state)
        return self.update_activity(state)

    def regular_update(self, state: State) -> list[MediaLibrary.Record]:
        self._update_tags(state)
        if state.special_day is not None:
            self.update_character(state)
        return self.update_activity(state)
