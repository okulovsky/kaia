from kaia.eaglesong.core.primitives import Image
from .media_library_manager import MediaLibraryManager


class ImageService:
    def __init__(self,
                 manager: MediaLibraryManager
                 ):
        self.manager = manager

    def get_image(self, tags: dict[str, str]):
        content = self.manager.get_content(tags)
        image = Image(
            content.content,
            None,
            content.file_id
        )
        return image

    def feedback(self, feedback: str) -> None:
        self.manager.feedback(feedback)






