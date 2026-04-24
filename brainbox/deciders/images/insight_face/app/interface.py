from foundation_kaia.marshalling import FileLike, service, JSON
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IInsightFace:
    @brainbox_endpoint
    def analyze(self, image: FileLike) -> list[JSON]:
        """Detects and analyzes faces in an image, returning per-face attribute data."""
        ...
