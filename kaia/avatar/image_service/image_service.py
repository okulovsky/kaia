from typing import *
from ..media_library_manager import MediaLibraryManager
from ..state import State, MemoryItem
from dataclasses import dataclass
from brainbox import File, MediaLibrary

@dataclass
class ImageMemoryItem(MemoryItem):
    image_file_name: str


@dataclass
class ImageMetadata:
    tags: dict


@dataclass
class ImageServiceSettings:
    manager: MediaLibraryManager
    record_to_description: Optional[Callable[[MediaLibrary.Record], str]] = None

class ImageService:
    def __init__(self,
                 settings: ImageServiceSettings
                 ):
        self.settings = settings

    def mlm_record_to_file(self, content: MediaLibraryManager.Record):
        image = File(
            content.file_id,
            content.content,
            File.Kind.Image
        )
        image.metadata = ImageMetadata(content.original_record.tags)
        return image

    def get_new_image(self, state: State) -> File:
        content = self.settings.manager.get_content(state.get_state())
        image = self.mlm_record_to_file(content)
        self.settings.manager.feedback(content.file_id, 'seen')
        state.add_memory(ImageMemoryItem(content.file_id))
        return image

    def _get_last_image_memory_item(self, state) -> ImageMemoryItem|None:
        last_image: ImageMemoryItem = (
            state.iterate_memory_reversed()
            .where(lambda z: isinstance(z, ImageMemoryItem))
            .first_or_default()
        )
        return last_image


    def feedback(self, state: State, feedback: str) -> None:
        last_image = self._get_last_image_memory_item(state)
        if last_image is None:
            return
        self.settings.manager.feedback(last_image.image_file_name, feedback)

    def get_current_image(self, state: State) -> File|None:
        last_image = self._get_last_image_memory_item(state)
        if last_image is None:
            return None
        content = self.settings.manager.get_content_by_id(last_image.image_file_name)
        return self.mlm_record_to_file(content)

    def get_current_image_description(self, state: State) -> str|None:
        if self.settings.record_to_description is None:
            return None
        last_image = self._get_last_image_memory_item(state)
        if last_image is None:
            return None
        self.settings.manager.feedback(last_image.image_file_name, 'description_requested')
        record = self.settings.manager.media_library[last_image.image_file_name]
        return self.settings.record_to_description(record)











