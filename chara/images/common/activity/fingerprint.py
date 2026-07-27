from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeFingerprint:
    name: str|None = None
    location: str | None = None
    season: str | None = None
    weather: str | None = None
    time_of_day: str | None = None
    special_day: str | None = None


@dataclass(frozen=True)
class ImageSetupFingerprint:
    character_name: str
    theme_fingerprint: ThemeFingerprint

    def stratification_key(self, fields: tuple[str, ...]) -> tuple:
        result = []
        for field_name in fields:
            if hasattr(self, field_name):
                result.append(getattr(self, field_name))
            else:
                result.append(getattr(self.theme_fingerprint, field_name))
        return tuple(result)


@dataclass(frozen=True)
class ImageFingerprint:
    setup_fingerprint: ImageSetupFingerprint
    activity: str

    def to_tags(self) -> dict[str, str]:
        tags = dict(character=self.setup_fingerprint.character_name, activity=self.activity)
        theme = self.setup_fingerprint.theme_fingerprint
        if theme.name is not None:
            tags['theme'] = theme.name
        for field_name in ('location', 'season', 'weather', 'time_of_day', 'special_day'):
            value = getattr(theme, field_name)
            if value is not None:
                tags[field_name] = value
        return tags
