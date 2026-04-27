import io

from PIL import Image

from interface import IWD14Tagger, FileLike
from foundation_kaia.brainbox_utils import SingleModelStorage
from foundation_kaia.marshalling import FileLikeHandler, JSON


class WD14TaggerService(IWD14Tagger):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def interrogate(self, image: FileLike, threshold: float = 0.35, model: str | None = None) -> dict[str, float]:
        interrogator = self.storage.get_model(model)
        data = FileLikeHandler.to_bytes(image)
        img = Image.open(io.BytesIO(data))
        result = interrogator.interrogate(img)[1]
        return {key: value for key, value in result.items() if value >= threshold}

    def tags(self, model: str | None = None, count: int | None = None) -> list[dict[str, JSON]]:
        interrogator = self.storage.get_model(model)
        tags = [row[1].to_dict() for row in interrogator.tags.iterrows()]
        if count is not None:
            tags = tags[:count]
        return tags
