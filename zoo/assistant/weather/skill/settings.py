from dataclasses import dataclass

@dataclass
class WeatherSettings:
    latitude: float
    longitude: float
    timezone: str
    forecast_for_next_day_from_hour: int = 17
    forecast_from_hour: int = 10
    forecast_to_hour: int = 18