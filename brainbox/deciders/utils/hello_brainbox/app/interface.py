from foundation_kaia.marshalling import FileLike, service, JSON
from foundation_kaia.brainbox_utils import brainbox_endpoint, brainbox_websocket, BrainboxReportItem
from typing import Iterable


@service
class IHelloBrainBox:
    @brainbox_endpoint
    def sum(self, a: int|float, b: int|float) -> float:
        """Returns the sum of two numbers (demo endpoint)."""
        ...

    @brainbox_endpoint
    def voiceover(self, text: str, model: str|None = None) -> FileLike:
        """Synthesizes speech for the given text (demo endpoint)."""
        ...

    @brainbox_endpoint
    def voice_embedding(self, file: FileLike) -> list[float]:
        """Computes a speaker embedding vector from an audio file (demo endpoint)."""
        ...

    @brainbox_endpoint
    def voice_clone(self, original: FileLike, model: str|None = None) -> FileLike:
        """Clones a voice from a reference audio file (demo endpoint)."""
        ...

    @brainbox_endpoint
    def use_resource(self, resource_name: str) -> FileLike:
        """Returns a resource file registered under the given name (demo endpoint)."""
        ...

    @brainbox_websocket
    def stream_voiceover(self, tokens: Iterable[dict[str,JSON]]) -> Iterable[bytes]:
        """Streams synthesized audio chunks from a token sequence (demo websocket endpoint)."""
        ...

    @brainbox_websocket
    def training(self, dataset: FileLike, raise_exception: bool = False, pause: float = 0.1, steps: int = 10) -> Iterable[BrainboxReportItem[str]]:
        """Runs a simulated training loop with streaming progress reports (demo websocket endpoint)."""
        ...


