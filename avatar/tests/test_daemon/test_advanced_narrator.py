from datetime import date, datetime
from unittest import TestCase

from avatar.daemon.common import State, SpecialDay
from avatar.daemon.common.content import ContentFinder, InMemoryFeedbackStorage, NewContentStrategy
from avatar.daemon.image_service import ImageLibraryLoader
from avatar.daemon.narration_service import AdvancedNarrator, IStateFieldSetter, SpecialDayStateFieldSetter
from foundation_kaia.misc import Loc
from foundation_kaia.marshalling import Storage
from .media_library_fixture import write_media_library


class FixedFieldSetter(IStateFieldSetter):
    def __init__(self, field: str, value):
        self.field = field
        self.value = value

    def update(self, state: State, now: datetime) -> None:
        setattr(state, self.field, self.value)


class SpecialDayStateFieldSetterTestCase(TestCase):
    def setUp(self):
        self.setter = SpecialDayStateFieldSetter([
            SpecialDay(datetime(2020, 10, 31), 'Halloween'),
            SpecialDay(
                datetime(2020, 1, 1), 'Leap day madness',
                is_this_day_today=lambda today: today == date(today.year, 1, 1),
            ),
        ])

    def test_fixed_day_matches_regardless_of_year(self):
        state = State()
        self.setter.update(state, datetime(2027, 10, 31))
        self.assertEqual('Halloween', state.special_day)

    def test_callable_override_is_used_when_present(self):
        state = State()
        self.setter.update(state, datetime(2031, 1, 1))
        self.assertEqual('Leap day madness', state.special_day)

    def test_no_match_on_a_regular_day(self):
        state = State()
        self.setter.update(state, datetime(2026, 5, 5))
        self.assertIsNone(state.special_day)

    def test_clears_a_stale_value_when_no_longer_a_special_day(self):
        state = State(special_day='Halloween')
        self.setter.update(state, datetime(2026, 5, 5))
        self.assertIsNone(state.special_day)


class AdvancedNarratorTestCase(TestCase):
    def setUp(self):
        self.folder_holder = Loc.create_test_folder()
        self.folder = self.folder_holder.__enter__()
        records = [
            {'file_id': 'A/summer_good', 'tags': dict(character='A', activity='swimming', season='summer', good_weather=True)},
            {'file_id': 'A/winter_bad', 'tags': dict(character='A', activity='skiing', season='winter', good_weather=False)},
            {'file_id': 'B/summer_good', 'tags': dict(character='B', activity='reading', season='summer', good_weather=True, special_day='Halloween')},
        ]
        write_media_library(self.folder, records)
        loader = ImageLibraryLoader(Storage(self.folder), self.folder)
        self.records = loader.get_records()
        self.feedback_storage = InMemoryFeedbackStorage()
        self.finder = ContentFinder(NewContentStrategy(randomize=False))

    def tearDown(self):
        self.folder_holder.__exit__(None, None, None)

    def test_fuzzy_activity_degrades_when_exact_match_is_missing(self):
        narrator = AdvancedNarrator(
            self.records,
            self.feedback_storage,
            [FixedFieldSetter('special_day', None), FixedFieldSetter('season', 'summer'), FixedFieldSetter('good_weather', False)],
        )
        state = State(character='A')
        records = narrator.regular_update(state)
        self.assertEqual('swimming', state.activity)
        self.assertEqual(['A/summer_good'], [r.get_id() for r in records])

    def test_character_does_not_rotate_without_a_special_day(self):
        narrator = AdvancedNarrator(
            self.records,
            self.feedback_storage,
            [FixedFieldSetter('special_day', None), FixedFieldSetter('season', 'summer'), FixedFieldSetter('good_weather', True)],
        )
        state = State(character='A')
        narrator.regular_update(state)
        self.assertEqual('A', state.character)

    def test_character_rotates_on_a_special_day(self):
        narrator = AdvancedNarrator(
            self.records,
            self.feedback_storage,
            [FixedFieldSetter('special_day', 'Halloween'), FixedFieldSetter('season', 'summer'), FixedFieldSetter('good_weather', True)],
        )
        state = State(character='A')
        narrator.regular_update(state)
        self.assertEqual('B', state.character)
        self.assertEqual('Halloween', state.special_day)
        self.assertEqual('reading', state.activity)
