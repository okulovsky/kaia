import json

from interface import IEspeakPhonemizer, FileLike
from runner import run_espeak


class EspeakPhonemizerService(IEspeakPhonemizer):
    def phonemize(self, text: list[str], language: str = 'en-us', stress: bool = False) -> list[list[list[str]]]:
        return run_espeak(dict(text=text, language=language, stress=stress))

    def phonemize_to_file(self, text: list[str], language: str = 'en-us', stress: bool = False) -> FileLike:
        result = self.phonemize(text, language, stress)
        return json.dumps(result).encode()
