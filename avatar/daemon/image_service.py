from typing import Optional, Callable, Union
from .common import IMessage, State, ChatCommand, message_handler, ImageCommand, Confirmation, AvatarService
from .common.content_manager import MediaLibraryManager, MediaLibrary
from dataclasses import dataclass
import base64

@dataclass
class NewImageCommand(IMessage):
    pass


@dataclass
class HideImageCommand(IMessage):
    pass

@dataclass
class ImageFeedback(IMessage):
    feedback: str

@dataclass
class RestoreImageCommand(IMessage):
    pass

@dataclass
class ImageDescriptionCommand(IMessage):
    pass


class ImageService(AvatarService):
    NewImageCommand = NewImageCommand
    HideImageCommand = HideImageCommand
    ImageFeedback = ImageFeedback
    RestoreImageCommand = RestoreImageCommand
    ImageDescriptionCommand = ImageDescriptionCommand


    def __init__(self,
                 state: State,
                 media_library_manager: MediaLibraryManager,
                 record_to_description: Optional[Callable[[MediaLibrary.Record], str]] = None
                 ):
        self.state = state
        self.media_library_manager = media_library_manager
        self.record_to_description = record_to_description
        self.last_image_record: MediaLibrary.Record|None = None

    def requires_brainbox(self):
        return False

    def _get_image_command(self, message: IMessage):
        return ImageCommand(
            base64.b64encode(self.last_image_record.get_content()).decode('ascii'),
            self.last_image_record.tags,
            self.last_image_record.filename
        ).as_propagation_confirmation_to(message)

    def _get_empty_image(self, message: IMessage):
        return ImageCommand(base64.b64encode(_empty_image).decode('ascii')).as_propagation_confirmation_to(message)

    @message_handler
    def new_image(self, message: NewImageCommand) -> ImageCommand:
        record = self.media_library_manager.match().weak(self.state.__dict__).find_content()
        if record is None:
            return self._get_empty_image(message)
        self.last_image_record = record
        self.media_library_manager.feedback(record.filename, 'seen')
        return self._get_image_command(message)

    @message_handler
    def hide_image(self, message: HideImageCommand) -> ImageCommand:
        return self._get_empty_image(message)

    @message_handler
    def restore_image(self, message: RestoreImageCommand) -> ImageCommand:
        if self.last_image_record is None:
            return self._get_empty_image(message)
        return self._get_image_command(message)

    @message_handler
    def image_feedback(self, message: ImageFeedback) -> Confirmation:
        if self.last_image_record is None:
            return message.confirm_this("No image")
        self.media_library_manager.feedback(self.last_image_record.filename, message.feedback)
        return message.confirm_this()

    @message_handler
    def get_current_image_description(self, message: ImageDescriptionCommand) -> Union[Confirmation, ChatCommand]:
        if self.record_to_description is None:
            return message.confirm_this("No description method")
        if self.last_image_record is None:
            return message.confirm_this("No description")
        return ChatCommand(self.record_to_description(self.last_image_record), ChatCommand.MessageType.system)


_empty_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'