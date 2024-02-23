from unittest import TestCase
from datetime import datetime, timedelta
from kaia.eaglesong.core import Automaton, Scenario, Return
from zoo.assistant.skills.weather_skill import WeatherSkill, WeatherIntents, WeatherReply, get_sample


def S():
    return Scenario(automaton_factory=lambda: Automaton(WeatherSkill(
        0,
        0,
        'Europe/Berlin',
        lambda: datetime(2023,12,21,18,15),
        get_sample
    ).run, None))



class WeatherTestCase(TestCase):
    def test_weather(self):
        (
            S()
            .send(WeatherIntents.question.utter())
            .check(
                WeatherReply.weather.utter(
                    temperature_2m = 6.1,
                    weathercode = 3
                ).assertion,
                Return
            )
            .validate()
        )