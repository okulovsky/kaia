from foundation_kaia.marshalling_2 import FileLike, service, JSON
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IYolo:
    @brainbox_endpoint
    def analyze(self, image: FileLike, model: str | None = None) -> JSON:
        ...
