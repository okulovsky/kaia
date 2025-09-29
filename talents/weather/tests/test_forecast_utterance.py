from unittest import TestCase
from talents.weather.skill.templates import WeatherReply,Forecast, Precipitation


class WeatherReplyTestCase(TestCase):
    def test_reply(self): #This configuration actually should not happen
        f = Forecast(True, 10, 20, True, ())
        self.assertEqual(
            'The temperature today is between 10 and 20, mostly sunny, nothing.',
            WeatherReply.forecast.utter(f).to_str()
        )

    def test_reply_with_precipitations(self):
        f = Forecast(
            True, 10, 20, True,
            (
                Precipitation(61, 14),
                Precipitation(63, 16, 17)
            )
        )
        self.assertEqual(
            'The temperature today is between 10 and 20, mostly sunny, slight rain at 14 and moderate rain from 16 to 17.',
            WeatherReply.forecast.utter(f).to_str()
        )

    def test_precipications_set_to_none(self):
        f = Forecast(True, 10, 20, True, None)
        self.assertEqual(
            'The temperature today is between 10 and 20, mostly sunny, no precipitations.',
            WeatherReply.forecast.utter(f).to_str()
        )



