from foundation_kaia.marshalling import FileLike, service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class ICosyVoice:
    @brainbox_endpoint
    def train(self, voice: str, text: str, file: FileLike, model: str|None = None) -> None:
        """Registers a (text, audio) pair to create a named speaker voice for cloning."""
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voice_to_file(self, voice: str, file: FileLike, model: str|None = None) -> FileLike:
        """Converts audio to the target voice style via voice conversion."""
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voice_to_text(self, voice: str, text: str, model: str|None = None) -> FileLike:
        """Synthesizes the given text as speech in the named voice."""
        ...

    @brainbox_endpoint(content_type='audio/wav')
    def voice_to_text_translingual(self, voice: str, text: str, model: str|None = None) -> FileLike:
        """Synthesizes the given text as speech in the named voice across languages."""
        ...
