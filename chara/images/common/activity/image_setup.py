from dataclasses import dataclass
from chara.common import Character
from .theme import Theme
from .fingerprint import ThemeFingerprint, ImageSetupFingerprint


@dataclass
class ImageSetup:
    character: Character
    theme: Theme

    def to_fingerprint(self) -> ImageSetupFingerprint:
        theme_fingerprint = ThemeFingerprint(
            name = self.theme.name,
            location=self.theme.location,
            season=self.theme.season,
            weather=self.theme.weather,
            time_of_day=self.theme.time_of_day,
            special_day=self.theme.special_day.name if self.theme.special_day is not None else None,
        )
        return ImageSetupFingerprint(self.character.name, theme_fingerprint)
