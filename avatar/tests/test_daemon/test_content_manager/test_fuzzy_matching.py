from collections import OrderedDict
from dataclasses import dataclass
from unittest import TestCase
from avatar.daemon.common.content_manager import DataClassDataProvider, DictDataProvider, ContentManager


@dataclass
class Record:
    content: str
    character: str
    season: str|None = None
    time_of_day: str|None = None
    weather: str|None = None
    filename: str = ''

    def __post_init__(self):
        if not self.filename:
            self.filename = self.content


def manager(*records: Record):
    return ContentManager[Record](DataClassDataProvider(list(records)))


def dict_manager(*records: dict):
    return ContentManager(DictDataProvider(list(records), 'filename'))


FUZZY = OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')])


class FuzzyMatchingTestCase(TestCase):
    def test_fuzzy_full_match_needs_no_drop(self):
        m = manager(
            Record('exact', 'A', season='summer', time_of_day='morning', weather='sunny'),
            Record('other', 'A', season='winter', time_of_day='evening', weather='snowy'),
        )
        result = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')]))
            .find_content()
        )
        self.assertEqual('exact', result.content)

    def test_fuzzy_drops_last_key_first(self):
        # weather is the last (lowest-priority) key, so it is dropped before season/time_of_day.
        m = manager(
            Record('close', 'A', season='summer', time_of_day='morning', weather='rainy'),
            Record('far', 'A', season='winter', time_of_day='evening', weather='sunny'),
        )
        result = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')]))
            .find_content()
        )
        self.assertEqual('close', result.content)

    def test_fuzzy_drops_down_to_a_single_key(self):
        m = manager(
            Record('season_only', 'A', season='summer', time_of_day='evening', weather='rainy'),
            Record('unrelated', 'A', season='winter', time_of_day='evening', weather='rainy'),
        )
        result = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')]))
            .find_content()
        )
        self.assertEqual('season_only', result.content)

    def test_fuzzy_drops_all_the_way_to_strong_only(self):
        m = manager(
            Record('character_only', 'A', season='winter', time_of_day='evening', weather='rainy'),
        )
        result = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')]))
            .find_content()
        )
        self.assertEqual('character_only', result.content)

    def test_fuzzy_returns_none_when_strong_never_matches(self):
        m = manager(
            Record('wrong_character', 'B', season='summer', time_of_day='morning', weather='sunny'),
        )
        result = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')]))
            .find_content()
        )
        self.assertIsNone(result)

    def test_fuzzy_order_determines_which_record_survives(self):
        # Neither record matches all three tags; each matches all but one.
        matches_all_but_time_of_day = Record('by_season', 'A', season='summer', time_of_day='evening', weather='sunny')
        matches_all_but_season = Record('by_time_of_day', 'A', season='winter', time_of_day='morning', weather='sunny')

        m = manager(matches_all_but_time_of_day, matches_all_but_season)
        drop_weather_then_time_of_day = OrderedDict([('season', 'summer'), ('time_of_day', 'morning'), ('weather', 'sunny')])
        result = m.match().strong({'character': 'A'}).fuzzy(drop_weather_then_time_of_day).find_content()
        self.assertEqual('by_season', result.content)

        m = manager(matches_all_but_time_of_day, matches_all_but_season)
        drop_season_then_time_of_day = OrderedDict([('weather', 'sunny'), ('time_of_day', 'morning'), ('season', 'summer')])
        result = m.match().strong({'character': 'A'}).fuzzy(drop_season_then_time_of_day).find_content()
        self.assertEqual('by_time_of_day', result.content)

    def test_fuzzy_tag_set_to_none_passes(self):
        m = manager(
            Record('exact', 'A', season='summer', time_of_day='morning', weather='sunny'),
            Record('no_opinion', 'A'),
            Record('conflicting', 'A', season='winter', time_of_day='evening', weather='snowy'),
        )
        _, pool = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(FUZZY)
            .find_content_with_pool()
        )
        self.assertEqual(['exact', 'no_opinion'], sorted(r.original_record.content for r in pool))

    def test_fuzzy_tag_missing_passes(self):
        m = dict_manager(
            dict(filename='exact', character='A', season='summer', time_of_day='morning', weather='sunny'),
            dict(filename='no_season', character='A', time_of_day='morning', weather='sunny'),
            dict(filename='conflicting', character='A', season='winter', time_of_day='morning', weather='sunny'),
        )
        _, pool = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(FUZZY)
            .find_content_with_pool()
        )
        self.assertEqual(['exact', 'no_season'], sorted(r.filename for r in pool))

    def test_fuzzy_partially_none_record_survives_without_dropping(self):
        # 'partial' has no opinion on weather and matches the rest, so it passes at the
        # full cutoff - no fuzzy key has to be dropped, and the conflicting record stays out.
        m = manager(
            Record('partial', 'A', season='summer', time_of_day='morning'),
            Record('conflicting', 'A', season='summer', time_of_day='evening', weather='sunny'),
        )
        result = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(FUZZY)
            .find_content()
        )
        self.assertEqual('partial', result.content)

    def test_fuzzy_all_none_record_is_the_only_survivor(self):
        m = manager(
            Record('conflicting', 'A', season='winter', time_of_day='evening', weather='snowy'),
            Record('no_opinion', 'A'),
        )
        result = (
            m.match()
            .strong({'character': 'A'})
            .fuzzy(FUZZY)
            .find_content()
        )
        self.assertEqual('no_opinion', result.content)
