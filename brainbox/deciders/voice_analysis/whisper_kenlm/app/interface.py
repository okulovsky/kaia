from foundation_kaia.marshalling import FileLike, service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IWhisperKenLM:
    @brainbox_endpoint
    def train_lm(self, corpus: str) -> None:
        ...

    @brainbox_endpoint
    def transcribe(self, file: FileLike, weight: float = 0.5, beams: int = 5, languages: list[str] | None = None) -> str:
        """If `languages` is given, the spoken language is detected among these codes only (e.g. ['en', 'de', 'ru'])."""
        ...
