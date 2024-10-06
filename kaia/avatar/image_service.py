from kaia.eaglesong.core.primitives import Image
from .media_library_manager import MediaLibraryManager
from .state import State, MemoryItem
from dataclasses import dataclass

@dataclass
class ImageMemoryItem(MemoryItem):
    image_file_name: str



class ImageService:
    def __init__(self,
                 manager: MediaLibraryManager
                 ):
        self.manager = manager

    def get_image(self, state: State):
        content = self.manager.get_content(state.get_state())
        image = Image(
            content.content,
            None,
            content.file_id
        )
        self.manager.feedback(content.file_id, 'seen')
        state.add_memory(ImageMemoryItem(content.file_id))
        return image

    def feedback(self, state: State, feedback: str) -> None:
        last_image: ImageMemoryItem = state.iterate_memory_reversed().where(lambda z: isinstance(z, ImageMemoryItem)).first_or_default()
        if last_image is None:
            return
        self.manager.feedback(last_image.image_file_name, feedback)






