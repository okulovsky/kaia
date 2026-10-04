from dataclasses import dataclass
from avatar.daemon.common import SpecialDay

DARK_EVENING_SEASONS = ('winter',)


@dataclass
class Theme:
    name: str|None = None
    description: str|None = None
    location: str|None = None
    season: str | None = None
    good_weather: bool|None = None
    time_of_day: str|None = None
    special_day: SpecialDay|None = None

    def _is_dark(self) -> bool:
        if self.time_of_day == 'night':
            return True
        return self.time_of_day == 'evening' and self.season in DARK_EVENING_SEASONS

    def _weather_phrase(self) -> str:
        if self.good_weather:
            if self._is_dark():
                return "The sky is clear and starry. "
            return "The weather is sunny. "
        if self.season == 'winter':
            return "The weather is snowy. "
        return "The weather is rainy. "

    def full_text(self):
        result = []

        time_parts = []
        if self.special_day is not None:
            time_parts.append(self.special_day.name)
        if self.season is not None:
            time_parts.append(self.season)
        if self.time_of_day is not None:
            time_parts.append(self.time_of_day)
        if len(time_parts) > 0:
            result.append("It is "+", ".join(time_parts)+". ")

        if self.location is not None:
            result.append(f"The image takes place {self.location}. ")
        if self.good_weather is not None:
            result.append(self._weather_phrase())
        if self.name is not None:
            result.append(f"The theme of the image is {self.name}")
            if self.description is not None:
                result.append(f' ({self.description})')
            result.append('.')

        return ''.join(result).strip()







