from typing import *
from .templates import WeatherIntents, WeatherReply
from kaia.kaia.core import SingleLineKaiaSkill
from datetime import datetime
from .request import get_open_meteo, parse_open_meteo
from kaia.dub.core import Utterance
from .forecast import make_forecast, convert_forecast_to_utterance
from .settings import WeatherSettings



class WeatherSkill(SingleLineKaiaSkill):
    def __init__(self,
                 settings: WeatherSettings,
                 datetime_factory: Callable = datetime.now,
                 request_caller: Optional[Callable] = None
    ):
        super().__init__(
            WeatherIntents,
            WeatherReply,
        )
        self.settings = settings
        self.datetime_factory = datetime_factory
        self.request_caller = request_caller if request_caller is not None else self._make_request

    def _make_request(self):
        return get_open_meteo(self.settings.latitude, self.settings.longitude, self.settings.timezone)

    def run(self):
        intent: Utterance = yield None
        if intent.template == WeatherIntents.question:
            reply = self.request_caller()
            time = self.datetime_factory()
            info = parse_open_meteo(time, reply)
            yield WeatherReply.weather.utter(**info)
        elif intent.template == WeatherIntents.forecast:
            data = self.request_caller()
            time = self.datetime_factory()
            forecast = make_forecast(data, time, self.settings)
            reply = convert_forecast_to_utterance(forecast)
            yield reply






