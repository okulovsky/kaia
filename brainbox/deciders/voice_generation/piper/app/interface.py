from foundation_kaia.marshalling import FileLike, service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IPiper:
    @brainbox_endpoint(content_type='audio/wav')
    def voiceover(self,
                  text: str,
                  model: str = 'en',
                  speaker: int | None = None,
                  noise_scale: float | None = None,
                  length_scale: float | None = None,
                  noise_w: float | None = None,
                  ) -> FileLike:
        ...

    @brainbox_endpoint
    def upload_tar_voice(self, tar_file: FileLike, name: str | None = None) -> None:
        ...

    @brainbox_endpoint
    def delete_voice(self, name: str) -> None:
        ...
