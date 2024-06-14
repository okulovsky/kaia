from typing import *
from .templates import WeatherIntents, WeatherReply
from kaia.kaia.core import SingleLineKaiaSkill
from datetime import datetime
from .request import get_open_meteo, parse_open_meteo



class WeatherSkill(SingleLineKaiaSkill):
    def __init__(self,
                 latitude: float,
                 longitude: float,
                 timezone: str,
                 datetime_factory: Callable = datetime.now,
                 request_caller: Optional[Callable] = None
    ):
        super().__init__(
            WeatherIntents,
            WeatherReply,
        )
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.datetime_factory = datetime_factory
        self.request_caller = request_caller if request_caller is not None else self._make_request

    def _make_request(self):
        return get_open_meteo(self.latitude, self.longitude, self.timezone)

    def run(self):
        reply = self.request_caller()
        time = self.datetime_factory()
        info = parse_open_meteo(time, reply)
        yield WeatherReply.weather.utter(**info)




