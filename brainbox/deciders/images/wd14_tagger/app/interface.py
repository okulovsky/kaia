from foundation_kaia.marshalling import FileLike, service, JSON
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IWD14Tagger:
    @brainbox_endpoint
    def interrogate(self, image: FileLike, threshold: float = 0.35, model: str | None = None) -> dict[str, float]:
        """Tags an image and returns label-to-confidence pairs above the threshold."""
        ...

    @brainbox_endpoint
    def tags(self, model: str | None = None, count: int | None = None) -> list[dict[str,JSON]]:
        """Returns all known tags for a model, optionally limited by count."""
        ...
