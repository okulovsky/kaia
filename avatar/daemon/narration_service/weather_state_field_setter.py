from datetime import datetime
import requests
from loguru import logger
from ..common import State
from .state_field_setter import IStateFieldSetter


class WeatherStateFieldSetter(IStateFieldSetter):
    PRECIPITATION_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}

    def __init__(self,
                 latitude: float,
                 longitude: float,
                 timezone: str,
                 cooldown_in_seconds: int = 60 * 60,
                 ):
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.cooldown_in_seconds = cooldown_in_seconds
        self.last_fetch_time: datetime | None = None

    def _get_open_meteo(self) -> dict:
        reply = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params=dict(
                latitude=self.latitude,
                longitude=self.longitude,
                hourly='temperature_2m,weathercode',
                timezone=self.timezone,
            )
        )
        return reply.json()

    def _parse_open_meteo(self, now: datetime, reply: dict) -> dict | None:
        for i, t in enumerate(reply['hourly']['time']):
            if datetime.fromisoformat(t) > now:
                return {name: reply['hourly'][name][i] for name in ('temperature_2m', 'weathercode')}
        return None

    def _code_to_tag(self, code: int, season: str | None) -> str:
        if code in self.PRECIPITATION_CODES:
            return 'snowy' if season == 'winter' else 'rainy'
        return 'sunny'

    def update(self, state: State, now: datetime) -> None:
        if self.last_fetch_time is not None and (now - self.last_fetch_time).total_seconds() < self.cooldown_in_seconds:
            return
        try:
            reply = self._get_open_meteo()
            info = self._parse_open_meteo(now, reply)
            if info is not None:
                state.weather = self._code_to_tag(info['weathercode'], state.season)
        except Exception:
            logger.exception('WeatherStateFieldSetter failed to fetch weather')
        finally:
            self.last_fetch_time = now
