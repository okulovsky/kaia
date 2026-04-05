from foundation_kaia.marshalling_2 import FileLike, service, JSON
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IWD14Tagger:
    @brainbox_endpoint
    def interrogate(self, image: FileLike, threshold: float = 0.35, model: str | None = None) -> dict[str, float]:
        ...

    @brainbox_endpoint
    def tags(self, model: str | None = None, count: int | None = None) -> list[dict[str,JSON]]:
        ...
