import json
from typing import Iterable

from interface import IHelloBrainBox, FileLike
from training import HelloBrainBoxTrainingProcess
from foundation_kaia.brainbox_utils import SingleModelStorage, BrainboxReportItem
from foundation_kaia.marshalling_2 import FileLikeHandler, JSON


class HelloBrainBoxService(IHelloBrainBox):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def sum(self, a: int|float, b: int|float) -> float:
        return a+b

    def voiceover(self, text: str, model: str|None = None) -> FileLike:
        m = self.storage.get_model(model)
        return json.dumps(dict(text=text, model=str(m))).encode()

    def voice_embedding(self, file: FileLike) -> list[float]:
        result = [0 for _ in range(10)]
        for c in FileLikeHandler.to_bytes(file):
            if ord(b'0')<=c and c<=ord(b'9'):
                result[c-ord(b'0')] += 1
        return result

    def stream_voiceover(self, tokens: Iterable[dict[str,JSON]]) -> Iterable[bytes]:
        for token in tokens:
            yield json.dumps(dict(token=token['text'])).encode()

    def training(self, dataset: FileLike, raise_exception: bool = False, pause: float = 0.1, steps: int = 10) -> Iterable[BrainboxReportItem[str]]:
        FileLikeHandler.write(dataset, "/resources/dataset")
        return HelloBrainBoxTrainingProcess(raise_exception, pause, steps).start_process('/resources/log.html')
