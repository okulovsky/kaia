from foundation_kaia.marshalling_2 import FileLike, service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IChatterbox:
    @brainbox_endpoint
    def train(self, speaker: str, file: FileLike) -> None:
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voiceover(
        self,
        text: str,
        speaker: str,
        language: str = 'en',
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
    ) -> FileLike:
        ...
