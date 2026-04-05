from interface import IInsightFace, FileLike
from foundation_kaia.brainbox_utils import SingleModelStorage
from foundation_kaia.marshalling_2 import FileLikeHandler, JSON


class InsightFaceService(IInsightFace):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def analyze(self, image: FileLike) -> list[JSON]:
        embedder = self.storage.get_model(None)
        data = FileLikeHandler.to_bytes(image)
        return embedder.extract_embeddings(data)
