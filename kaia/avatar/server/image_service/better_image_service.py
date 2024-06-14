from kaia.eaglesong.core.primitives import Image
from .image_service import IImageService
from .strategy import IImageServiceStrategy
from .feedback_provider import FeedbackProvider
from pathlib import Path
from kaia.brainbox import MediaLibrary

class ImageService(IImageService):
    def __init__(self,
                 strategy: IImageServiceStrategy,
                 media_library_path: Path,
                 feedback_file_path: Path,
                 ):
        self.strategy = strategy
        self.media_library = MediaLibrary.read(media_library_path)
        self.feedback_provider = FeedbackProvider(feedback_file_path)
        self.last_image_id: None | str = None


    def get_image(self, tags: dict[str, str]):
        ml = self.media_library

        filtered_ids = set()
        for record in ml.records:
            ok = True
            for key, value in tags.items():
                if record.tags[key] != value:
                    ok = False
                    break
            if not ok:
                continue
            filtered_ids.add(record.filename)

        ml = ml.limit_to(filtered_ids)
        ml = self.feedback_provider.add_feedback_to_media_library(ml)
        choosen_id = self.strategy.choose_image_filename(ml)
        if choosen_id is None:
            self.last_image_id = None
            raise ValueError('Cannot find image')
        self.last_image_id = choosen_id
        self.feedback_provider.append_feedback(self.last_image_id, dict(seen=1))
        image = Image(
            ml.mapping[choosen_id].get_content(),
            None,
            choosen_id
        )
        return image

    def feedback(self, feedback: str) -> None:
        if self.last_image_id is None:
            raise ValueError(f'No image was sent, so no feedback is going to be provided')
        self.feedback_provider.append_feedback(self.last_image_id, {feedback:1})






