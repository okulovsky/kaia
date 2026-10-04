from foundation_kaia.marshalling import FileLike, service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IParlerTts:
    @brainbox_endpoint
    def train(self, speaker: str, description: str) -> None:
        """Registers a natural-language voice description under a speaker name."""
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voiceover(
        self,
        text: str,
        speaker: str,
        model: str | None = None,
        temperature: float = 1.0,
        seed: int | None = None,
    ) -> FileLike:
        """Synthesizes speech for the given text with the voice registered as `speaker`."""
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voiceover_with_description(
        self,
        text: str,
        description: str,
        model: str | None = None,
        temperature: float = 1.0,
        seed: int | None = None,
    ) -> FileLike:
        """Synthesizes speech for the given text with an ad-hoc voice description."""
        ...

    @brainbox_endpoint
    def get_speakers(self) -> dict[str, str]:
        """Returns the registered speakers along with their voice descriptions."""
        ...
