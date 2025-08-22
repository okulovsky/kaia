from unittest import TestCase
from datetime import datetime
from eaglesong.core import Automaton, Scenario, Return
from talents.weather.skill.skill import *
from talents.weather.skill.templates import *
from talents.weather.skill.request import get_sample


def S(hour=21):
    return Scenario(automaton_factory=lambda: Automaton(WeatherSkill(
        WeatherSettings(0,0,'Europe/Berlin'),
        lambda: datetime(2023,12,21,hour,15),
        get_sample
    ).run, None))



class WeatherTestCase(TestCase):
    def test_weather(self):
        (
            S()
            .send(WeatherIntents.question.utter())
            .check(
                WeatherReply.weather.utter(
                    TEMPERATURE.assign(4),
                    WEATHER_CODE.assign(80)
                ),
                Return
            )
            .validate()
        )



    def test_forecast_today(self):
        result = (
            S(14)
            .send(WeatherIntents.forecast.utter())
            .check(Scenario.stash('forecast'), Return)
            .validate()
        )
        val = result.stashed_values['forecast'].value.__dict__
        true =  {'for_today': True, 'min_t': 6, 'max_t': 8, 'is_sunny': False, 'precipitations': (Precipitation(weather_code=61, start=14, end=None), Precipitation(weather_code=63, start=15, end=None), Precipitation(weather_code=61, start=16, end=None))}
        self.assertEqual(str(true), str(val))



    def test_forecast_tomorrow(self):
        (
            S(20)
            .send(WeatherIntents.forecast.utter())
            .check(WeatherReply.forecast.utter(Forecast(
                for_today=False,
                min_t = 2,
                max_t = 3,
                is_sunny = True,
                precipitations = ()
            )), Return)
            .validate()
        )
