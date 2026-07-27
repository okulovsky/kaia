from dataclasses import dataclass
from avatar.daemon.common import SpecialDay

@dataclass
class Theme:
    name: str|None = None
    description: str|None = None
    location: str|None = None
    season: str | None = None
    weather: str|None = None
    time_of_day: str|None = None
    special_day: SpecialDay|None = None

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
        if self.weather is not None:
            result.append(f"The weather is {self.weather}. ")
        if self.name is not None:
            result.append(f"The theme of the image is {self.name}")
            if self.description is not None:
                result.append(f' ({self.description})')
            result.append('.')

        return ''.join(result).strip()







