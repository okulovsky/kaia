from typing import *
from . import templates as t
from kaia.kaia import SingleLineKaiaSkill
from datetime import datetime
from .request import get_open_meteo, parse_open_meteo
from eaglesong.templates import Utterance
from .forecast import make_forecast
from .settings import WeatherSettings



class WeatherSkill(SingleLineKaiaSkill):
    def __init__(self,
                 settings: WeatherSettings,
                 datetime_factory: Callable = datetime.now,
                 request_caller: Optional[Callable] = None
    ):
        super().__init__(
            t.WeatherIntents,
            t.WeatherReply,
        )
        self.settings = settings
        self.datetime_factory = datetime_factory
        self.request_caller = request_caller if request_caller is not None else self._make_request

    def _make_request(self):
        return get_open_meteo(self.settings.latitude, self.settings.longitude, self.settings.timezone)

    def run(self):
        intent: Utterance = yield None
        if intent in t.WeatherIntents.question:
            reply = self.request_caller()
            time = self.datetime_factory()
            info = parse_open_meteo(time, reply)
            yield t.WeatherReply.weather.utter(
                t.WEATHER_CODE.assign(info['weathercode']),
                t.TEMPERATURE.assign(int(info['temperature_2m']))
            )
        elif intent.template == t.WeatherIntents.forecast:
            data = self.request_caller()
            time = self.datetime_factory()
            forecast = make_forecast(data, time, self.settings)
            yield t.WeatherReply.forecast.utter(forecast)






