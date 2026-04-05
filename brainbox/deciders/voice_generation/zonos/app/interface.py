from foundation_kaia.marshalling_2 import FileLike, service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IZonos:
    @brainbox_endpoint
    def train(self, speaker: str, sample: FileLike) -> None:
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voiceover(self,
                  text: str,
                  speaker: str,
                  language: str = 'en-us',
                  emotion: list[float] | None = None,
                  speaking_rate: float | None = None,
                  ) -> FileLike:
        ...
