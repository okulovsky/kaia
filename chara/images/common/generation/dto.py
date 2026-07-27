from dataclasses import dataclass, field
from ..activity import ImageFingerprint, ImageSetup
from ..drawing import DrawingCase

@dataclass
class MediaLibraryDescriptionItem:
    file_id: str
    image_fingerprint: ImageFingerprint
    case: DrawingCase|None = None


@dataclass
class ActivityStatistics:
    generated: int = 0
    seen: int = 0
    good: int = 0
    bad: int = 0


@dataclass
class ImageSetupStatistics:
    setup: ImageSetup
    activity_status: dict[str, ActivityStatistics] = field(default_factory=dict)