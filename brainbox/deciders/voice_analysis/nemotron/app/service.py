from typing import Iterable
from interface import INemotron, FileLike
from audio import PcmStreamDecoder, decode_all
from foundation_kaia.brainbox_utils import SingleModelStorage
from foundation_kaia.marshalling import FileLikeHandler, JSON


DEFAULT_MODEL = 'multilingual'


class NemotronService(INemotron):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def transcribe(self, file: FileLike, language: str = 'auto', model: str | None = None) -> JSON:
        recognizer = self.storage.get_model(model or DEFAULT_MODEL)
        samples, sample_rate = decode_all(FileLikeHandler.to_bytes(file))
        return recognizer.recognize(samples, sample_rate, language)

    def transcribe_stream(
            self,
            audio: Iterable[bytes] | FileLike,
            language: str = 'auto',
            sample_rate: int = 16000,
            model: str | None = None,
    ) -> Iterable[dict[str, JSON]]:
        for _, result in self._transcribe_streams(audio, [language], sample_rate, model):
            yield result

    def transcribe_stream_languages(
            self,
            audio: Iterable[bytes] | FileLike,
            languages: list[str],
            sample_rate: int = 16000,
            model: str | None = None,
    ) -> Iterable[dict[str, JSON]]:
        for language, result in self._transcribe_streams(audio, languages, sample_rate, model):
            yield dict(result, stream=language)

    def _transcribe_streams(self, audio, languages: list[str], sample_rate: int, model: str | None):
        # The audio is decoded once and pushed to a stream per language
        recognizer = self.storage.get_model(model or DEFAULT_MODEL)
        decoder = PcmStreamDecoder(sample_rate)
        streams = {}
        try:
            for language in languages:
                streams[language] = recognizer.open_stream(language)
            for chunk in FileLikeHandler.to_bytes_iterable(audio):
                samples = decoder.feed(chunk)
                if samples is None:
                    continue
                for language, stream in streams.items():
                    stream.push(samples, decoder.sample_rate)
                    for result in stream.poll():
                        yield language, result
            for language, stream in streams.items():
                stream.finish()
                for result in stream.poll():
                    yield language, result
        finally:
            for stream in streams.values():
                stream.close()
