import json
import zipfile
from datetime import date, datetime
from unittest import TestCase

from avatar.daemon.common import State, SpecialDay
from avatar.daemon.common.content_manager import NewContentStrategy
from avatar.daemon.image_service import MediaLibrary, MediaLibraryManager
from avatar.daemon.narration_service import AdvancedNarrator, IStateFieldSetter, SpecialDayStateFieldSetter
from foundation_kaia.misc import Loc


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
            {'path': 'A/summer_sunny', 'tags': dict(character='A', activity='swimming', season='summer', weather='sunny')},
            {'path': 'A/winter_snowy', 'tags': dict(character='A', activity='skiing', season='winter', weather='snowy')},
            {'path': 'B/summer_sunny', 'tags': dict(character='B', activity='reading', season='summer', weather='sunny')},
        ]
        with zipfile.ZipFile(self.folder/'media_library.zip', 'w') as zp:
            zp.writestr('records.json', json.dumps(records))
        media_library = MediaLibrary.from_folder(self.folder, 'media_library', '.zip')
        self.content_manager = MediaLibraryManager(media_library, strategy=NewContentStrategy(randomize=False))

    def tearDown(self):
        self.folder_holder.__exit__(None, None, None)

    def test_fuzzy_activity_degrades_when_exact_match_is_missing(self):
        narrator = AdvancedNarrator(
            self.content_manager,
            [FixedFieldSetter('special_day', None), FixedFieldSetter('season', 'summer'), FixedFieldSetter('weather', 'rainy')],
        )
        state = State(character='A')
        records = narrator.regular_update(state)
        self.assertEqual('swimming', state.activity)
        self.assertEqual(['A/summer_sunny'], [r.path for r in records])

    def test_character_does_not_rotate_without_a_special_day(self):
        narrator = AdvancedNarrator(
            self.content_manager,
            [FixedFieldSetter('special_day', None), FixedFieldSetter('season', 'summer'), FixedFieldSetter('weather', 'sunny')],
        )
        state = State(character='A')
        narrator.regular_update(state)
        self.assertEqual('A', state.character)

    def test_character_rotates_on_a_special_day(self):
        narrator = AdvancedNarrator(
            self.content_manager,
            [FixedFieldSetter('special_day', 'Halloween'), FixedFieldSetter('season', 'summer'), FixedFieldSetter('weather', 'sunny')],
        )
        state = State(character='A')
        narrator.regular_update(state)
        self.assertEqual('B', state.character)
        self.assertEqual('Halloween', state.special_day)
        self.assertEqual('reading', state.activity)
