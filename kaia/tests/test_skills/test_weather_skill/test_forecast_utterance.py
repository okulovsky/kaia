from unittest import TestCase
from kaia.skills.weather.templates import WeatherReply,Forecast, Precipitation


class WeatherReplyTestCase(TestCase):
    def test_reply(self):
        f = Forecast(True, 10, 20, True, ())
        self.assertEquals(
            'The temperature today is between 10 and 20, mostly sunny, no precipitations.',
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
        self.assertEquals(
            'The temperature today is between 10 and 20, mostly sunny, slight rain at 14 and moderate rain from 16 to 17.',
            WeatherReply.forecast.utter(f).to_str()
        )



