from foundation_kaia.marshalling import FileLike, service, JSON
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IWhisper:
    @brainbox_endpoint
    def transcribe(
        self,
        file: FileLike,
        model: str | None = None,
        initial_prompt: str | None = None,
        options: dict[str,JSON] | None = None,
    ) -> dict:
        """Transcribes audio and returns the full Whisper JSON result including segments and metadata."""
        ...

    @brainbox_endpoint
    def transcribe_text(
        self,
        file: FileLike,
        model: str | None = None,
        initial_prompt: str | None = None,
        options: dict | None = None
    ) -> str:
        """Transcribes audio and returns only the recognized text."""
        ...
