from collections import OrderedDict
from dataclasses import dataclass
from unittest import TestCase
from avatar.daemon.common.content import ContentFinder, Feedback, IRecord


@dataclass
class Record(IRecord):
    content: str
    character: str
    season: str|None = None
    time_of_day: str|None = None
    weather: str|None = None
    filename: str = ''

    def __post_init__(self):
        if not self.filename:
            self.filename = self.content

    def get_id(self) -> str:
        return self.filename

    def get_tags(self) -> dict:
        return {key: value for key, value in self.__dict__.items() if key != 'filename'}


@dataclass
class DictRecord(IRecord):
    data: dict

    def get_id(self) -> str:
        return self.data['filename']

    def get_tags(self) -> dict:
        return {key: value for key, value in self.data.items() if key != 'filename' and value is not None}


FUZZY = OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')])


class FuzzyMatchingTestCase(TestCase):
    def setUp(self):
        self.finder = ContentFinder()
        self.feedback = Feedback()

    def _find(self, *records: Record, fuzzy=FUZZY):
        return self.finder.find(records, self.feedback, strong={'character': 'A'}, fuzzy=fuzzy)

    def test_fuzzy_full_match_needs_no_drop(self):
        result = self._find(
            Record('exact', 'A', season='summer', time_of_day='morning', weather='sunny'),
            Record('other', 'A', season='winter', time_of_day='evening', weather='snowy'),
        )
        self.assertEqual('exact', result.content)

    def test_fuzzy_drops_last_key_first(self):
        # weather is the last (lowest-priority) key, so it is dropped before season/time_of_day.
        result = self._find(
            Record('close', 'A', season='summer', time_of_day='morning', weather='rainy'),
            Record('far', 'A', season='winter', time_of_day='evening', weather='sunny'),
        )
        self.assertEqual('close', result.content)

    def test_fuzzy_drops_down_to_a_single_key(self):
        result = self._find(
            Record('season_only', 'A', season='summer', time_of_day='evening', weather='rainy'),
            Record('unrelated', 'A', season='winter', time_of_day='evening', weather='rainy'),
        )
        self.assertEqual('season_only', result.content)

    def test_fuzzy_drops_all_the_way_to_strong_only(self):
        result = self._find(
            Record('character_only', 'A', season='winter', time_of_day='evening', weather='rainy'),
        )
        self.assertEqual('character_only', result.content)

    def test_fuzzy_returns_none_when_strong_never_matches(self):
        result = self._find(
            Record('wrong_character', 'B', season='summer', time_of_day='morning', weather='sunny'),
        )
        self.assertIsNone(result)

    def test_fuzzy_order_determines_which_record_survives(self):
        # Neither record matches all three tags; each matches all but one.
        matches_all_but_time_of_day = Record('by_season', 'A', season='summer', time_of_day='evening', weather='sunny')
        matches_all_but_season = Record('by_time_of_day', 'A', season='winter', time_of_day='morning', weather='sunny')

        drop_weather_then_time_of_day = OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')])
        result = self._find(matches_all_but_time_of_day, matches_all_but_season, fuzzy=drop_weather_then_time_of_day)
        self.assertEqual('by_season', result.content)

        drop_season_then_time_of_day = OrderedDict([('weather', 'sunny'), ('time_of_day', 'morning'), ('season', 'summer')])
        result = self._find(matches_all_but_time_of_day, matches_all_but_season, fuzzy=drop_season_then_time_of_day)
        self.assertEqual('by_time_of_day', result.content)

    def test_fuzzy_tag_set_to_none_passes(self):
        pool = self.finder.select(
            [
                Record('exact', 'A', season='summer', time_of_day='morning', weather='sunny'),
                Record('no_opinion', 'A'),
                Record('conflicting', 'A', season='winter', time_of_day='evening', weather='snowy'),
            ],
            strong={'character': 'A'},
            fuzzy=FUZZY,
        )
        self.assertEqual(['exact', 'no_opinion'], sorted(r.content for r in pool))

    def test_fuzzy_tag_missing_passes(self):
        pool = self.finder.select(
            [
                DictRecord(dict(filename='exact', character='A', season='summer', time_of_day='morning', weather='sunny')),
                DictRecord(dict(filename='no_season', character='A', time_of_day='morning', weather='sunny')),
                DictRecord(dict(filename='conflicting', character='A', season='winter', time_of_day='morning', weather='sunny')),
            ],
            strong={'character': 'A'},
            fuzzy=FUZZY,
        )
        self.assertEqual(['exact', 'no_season'], sorted(r.get_id() for r in pool))

    def test_fuzzy_partially_none_record_survives_without_dropping(self):
        # 'partial' has no opinion on weather and matches the rest, so it passes at the
        # full cutoff - no fuzzy key has to be dropped, and the conflicting record stays out.
        result = self._find(
            Record('partial', 'A', season='summer', time_of_day='morning'),
            Record('conflicting', 'A', season='summer', time_of_day='evening', weather='sunny'),
        )
        self.assertEqual('partial', result.content)

    def test_fuzzy_all_none_record_is_the_only_survivor(self):
        result = self._find(
            Record('conflicting', 'A', season='winter', time_of_day='evening', weather='snowy'),
            Record('no_opinion', 'A'),
        )
        self.assertEqual('no_opinion', result.content)
