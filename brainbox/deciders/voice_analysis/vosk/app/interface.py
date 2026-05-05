from foundation_kaia.marshalling import FileLike, service, JSON
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IVosk:
    @brainbox_endpoint
    def transcribe(self, file: FileLike, model: str | None = None) -> JSON:
        """Transcribes audio and returns the raw Vosk JSON result."""
        ...

    @brainbox_endpoint
    def transcribe_to_array(self, file: FileLike, model: str | None = None) -> list[dict[str, JSON]]:
        """Transcribes audio and returns word-level result records."""
        ...

    @brainbox_endpoint
    def transcribe_to_string(self, file: FileLike, model: str | None = None) -> str:
        """Transcribes audio and returns the recognized text."""
        ...
