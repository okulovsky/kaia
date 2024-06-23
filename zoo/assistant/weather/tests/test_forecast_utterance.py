from unittest import TestCase
from zoo.assistant.weather.skill import WeatherReply
from zoo.assistant.weather.skill.forecast import Forecast, Precipitation

class WeatherReplyTestCase(TestCase):
    def test_reply(self):
        f = Forecast(True, 10, 20, True, None)
        self.assertEquals(
            'The temperature today is between 10 and 20, mostly sunny, no precipitations.',
            WeatherReply.forecast.utter(f.__dict__).to_str()
        )

    def test_reply_with_precipitations(self):
        f = Forecast(True, 10, 20, True, None)
        v = f.__dict__
        v['precipitations'] = [
            WeatherReply.precipitation.utter(code=61, start=14).to_str(),
            WeatherReply.precipitation.utter(code=63, start=16, end=17).to_str()
        ]
        self.assertEquals(
            'The temperature today is between 10 and 20, mostly sunny, slight rain at 14 and moderate rain from 16 to 17.',
            WeatherReply.forecast.utter(v).to_str()
        )



