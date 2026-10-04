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
        recognizer = self.storage.get_model(model or DEFAULT_MODEL)
        decoder = PcmStreamDecoder(sample_rate)
        stream = recognizer.open_stream(language)
        try:
            for chunk in FileLikeHandler.to_bytes_iterable(audio):
                samples = decoder.feed(chunk)
                if samples is None:
                    continue
                stream.push(samples, decoder.sample_rate)
                yield from stream.poll()
            stream.finish()
            yield from stream.poll()
        finally:
            stream.close()
