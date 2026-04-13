from foundation_kaia.marshalling import service, FileLike
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IEspeakPhonemizer:
    @brainbox_endpoint
    def phonemize(self, text: list[str], language: str = 'en-us', stress: bool = False) -> list[list[list[str]]]:
        ...

    @brainbox_endpoint(content_type='application/json')
    def phonemize_to_file(self, text: list[str], language: str = 'en-us', stress: bool = False) -> FileLike:
        ...
