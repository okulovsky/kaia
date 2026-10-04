from unittest import TestCase
from chara.images.common import Theme


class ThemeWeatherTextTestCase(TestCase):
    def _weather_sentence(self, **kwargs) -> str:
        text = Theme(location='outdoors', **kwargs).full_text()
        return [s.strip().rstrip('.') for s in text.split('. ') if 'weather' in s or 'sky' in s][0]

    def test_good_weather_at_daytime_is_sunny(self):
        for time_of_day in ('morning', 'day'):
            for season in ('winter', 'spring', 'summer', 'autumn'):
                self.assertEqual(
                    'The weather is sunny',
                    self._weather_sentence(good_weather=True, season=season, time_of_day=time_of_day),
                )

    def test_good_weather_at_night_is_starry(self):
        for season in ('winter', 'spring', 'summer', 'autumn'):
            self.assertEqual(
                'The sky is clear and starry',
                self._weather_sentence(good_weather=True, season=season, time_of_day='night'),
            )

    def test_good_weather_in_a_dark_evening_is_starry(self):
        for season in ('winter', 'autumn'):
            self.assertEqual(
                'The sky is clear and starry',
                self._weather_sentence(good_weather=True, season=season, time_of_day='evening'),
            )

    def test_good_weather_in_a_light_evening_is_sunny(self):
        for season in ('spring', 'summer'):
            self.assertEqual(
                'The weather is sunny',
                self._weather_sentence(good_weather=True, season=season, time_of_day='evening'),
            )

    def test_bad_weather_in_winter_is_snowy(self):
        for time_of_day in ('morning', 'day', 'evening', 'night'):
            self.assertEqual(
                'The weather is snowy',
                self._weather_sentence(good_weather=False, season='winter', time_of_day=time_of_day),
            )

    def test_bad_weather_outside_winter_is_rainy(self):
        for season in ('spring', 'summer', 'autumn'):
            self.assertEqual(
                'The weather is rainy',
                self._weather_sentence(good_weather=False, season=season, time_of_day='night'),
            )

    def test_unset_weather_produces_no_weather_sentence(self):
        text = Theme(location='indoors', time_of_day='night').full_text()
        self.assertNotIn('weather', text)
        self.assertNotIn('sky', text)
