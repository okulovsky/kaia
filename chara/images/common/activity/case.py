from dataclasses import dataclass, field
from chara import ICase
from chara.common import Character
from .theme import Theme
from .fingerprint import ImageSetupFingerprint
from .image_setup import ImageSetup


@dataclass
class ActivityCase(ICase):
    setup: ImageSetup
    activities: list[str] = field(default_factory=list)
    batch_size: int = 15

    @property
    def character(self) -> Character:
        return self.setup.character

    @property
    def theme(self) -> Theme:
        return self.setup.theme

    def to_fingerprint(self) -> ImageSetupFingerprint:
        return self.setup.to_fingerprint()
