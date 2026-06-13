from foundation_kaia.marshalling import service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IChroma:
    @brainbox_endpoint
    def train(self, utterances: list[dict], collection_name: str|None = None) -> None:
        ...

    @brainbox_endpoint
    def find_neighbors(self, text: str, k: int = 5, collection_name: str|None = None) -> list[dict]:
        ...

    @brainbox_endpoint
    def get_vector(self, text: str) -> list[float]:
        ...
