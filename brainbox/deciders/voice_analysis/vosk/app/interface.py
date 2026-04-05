from foundation_kaia.marshalling_2 import FileLike, service, JSON
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IVosk:
    @brainbox_endpoint
    def transcribe(self, file: FileLike, model: str | None = None) -> JSON:
        ...

    @brainbox_endpoint
    def transcribe_to_array(self, file: FileLike, model: str | None = None) -> list[dict[str, JSON]]:
        ...

    @brainbox_endpoint
    def transcribe_to_string(self, file: FileLike, model: str | None = None) -> str:
        ...
