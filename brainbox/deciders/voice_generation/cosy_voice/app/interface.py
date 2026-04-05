from foundation_kaia.marshalling_2 import FileLike, service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class ICosyVoice:
    @brainbox_endpoint
    def train(self, voice: str, text: str, file: FileLike, model: str|None = None) -> None:
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voice_to_file(self, voice: str, file: FileLike, model: str|None = None) -> FileLike:
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voice_to_text(self, voice: str, text: str, model: str|None = None) -> FileLike:
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voice_to_text_translingual(self, voice: str, text: str, model: str|None = None) -> FileLike:
        ...
