import random
from typing import Optional, Callable, Union
from ..common import IMessage, State, TickEvent, ChatCommand, message_handler, ImageCommand, Confirmation, AvatarService, InitializationEvent
from ..common.content_manager import IFeedbackProvider, FileFeedbackProvider
from .media_library import MediaLibrary
from ...app import AvatarApi
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class NewImageCommand(IMessage):
    pass


@dataclass
class PhotoAlbumCommand(IMessage):
    records: list = field(default_factory=list)


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

@dataclass
class ImageVariantRequest(IMessage):
    variant_type: str
    time_to_show_in_seconds: int|None = None


class ImageService(AvatarService):
    NewImageCommand = NewImageCommand
    PhotoAlbumCommand = PhotoAlbumCommand
    HideImageCommand = HideImageCommand
    ImageFeedback = ImageFeedback
    RestoreImageCommand = RestoreImageCommand
    ImageDescriptionCommand = ImageDescriptionCommand
    VariantRequest = ImageVariantRequest

    MEDIA_LIBRARY_PREFIX = 'media_library'
    MEDIA_LIBRARY_SUFFIX = '.zip'
    DESCRIPTION_SUFFIX = '.description.json'

    def __init__(self,
                 state: State,
                 api: AvatarApi|None,
                 record_to_description: Optional[Callable[[MediaLibrary.Record], str]] = None
                 ):
        self.state = state
        self.api = api
        self.record_to_description = record_to_description
        self.last_base_image_record: MediaLibrary.Record|None = None
        self.last_shown_image_record: MediaLibrary.Record|None = None
        self.empty_image_uploaded: bool = False
        self.media_library: MediaLibrary|None = None
        self.feedback_provider: IFeedbackProvider|None = None
        self.current_records: list[MediaLibrary.Record] = []
        self.shown_this_round: set[str] = set()
        self.reset_timestamp: datetime|None = None

    @message_handler
    def on_initialize(self, message: InitializationEvent) -> None:
        self.media_library = MediaLibrary.from_folder(self.resources_folder, ImageService.MEDIA_LIBRARY_PREFIX, ImageService.MEDIA_LIBRARY_SUFFIX)
        self.feedback_provider = FileFeedbackProvider(self.resources_folder/'images-feedback.json')

    def requires_brainbox(self):
        return False

    def _get_image_command(self, message: IMessage):
        if self.api is not None:
            self.api.cache.upload(self.last_base_image_record.path, self.last_base_image_record.get_content())
        return ImageCommand(
            self.last_base_image_record.path,
            self.last_base_image_record.tags,
        ).as_propagation_confirmation_to(message)

    def _get_empty_image(self, message: IMessage):
        if self.api is not None and not self.empty_image_uploaded:
            self.api.cache.upload('empty_image.png', _empty_image)
        return ImageCommand('empty_image.png').as_propagation_confirmation_to(message)

    def _pick_next(self) -> MediaLibrary.Record|None:
        feedback = self.feedback_provider.load_feedback()
        available = [r for r in self.current_records if feedback.get(r.path, {}).get('bad', 0) == 0]
        if len(available) == 0:
            return None
        unshown = [r for r in available if r.path not in self.shown_this_round]
        pool = unshown if len(unshown) > 0 else available
        record = random.choice(pool)
        self.shown_this_round.add(record.path)
        return record

    def _show(self, message: IMessage) -> ImageCommand:
        record = self._pick_next()
        if record is None:
            self.last_shown_image_record = None
            return self._get_empty_image(message)
        self.last_base_image_record = record
        self.last_shown_image_record = record
        self.feedback_provider.append_feedback(record.path, {'seen': 1})
        return self._get_image_command(message)

    @message_handler
    def on_photo_album(self, message: PhotoAlbumCommand) -> ImageCommand:
        self.current_records = list(message.records)
        self.shown_this_round = set()
        return self._show(message)

    @message_handler
    def new_image(self, message: NewImageCommand) -> ImageCommand:
        return self._show(message)

    @message_handler
    def hide_image(self, message: HideImageCommand) -> ImageCommand:
        return self._get_empty_image(message)

    @message_handler
    def restore_image(self, message: RestoreImageCommand) -> ImageCommand:
        if self.last_base_image_record is None:
            return self._get_empty_image(message)
        return self._get_image_command(message)

    @message_handler
    def image_feedback(self, message: ImageFeedback) -> Confirmation:
        if self.last_shown_image_record is None:
            return message.error_on_this("No image")
        self.feedback_provider.append_feedback(self.last_shown_image_record.path, {message.feedback: 1})
        if self.last_shown_image_record.path != self.last_base_image_record.path:
            key = '_'.join(['variant', self.last_shown_image_record.tags['variant_type'], message.feedback])
            self.feedback_provider.append_feedback(self.last_base_image_record.path, {key: 1})
        return message.confirm_this()

    @message_handler
    def on_variant_request(self, cmd: ImageVariantRequest):
        if self.last_base_image_record is None:
            yield Confirmation(False).as_confirmation_for(cmd)
            return

        self.feedback_provider.append_feedback(self.last_base_image_record.path, {f'variant_requested_{cmd.variant_type}': 1})

        feedback = self.feedback_provider.load_feedback()
        records = [
            r for r in self.media_library.records
            if r.tags.get('original', '') == self.last_base_image_record.path
            and r.tags.get('variant_type', '') == cmd.variant_type
            and feedback.get(r.path, {}).get('bad', 0) == 0
        ]

        if len(records) == 0:
            yield Confirmation(False).as_confirmation_for(cmd)
            return

        record: MediaLibrary.Record = random.choice(records)
        self.api.cache.upload(record.path, record.get_content())
        if cmd.time_to_show_in_seconds is not None:
            self.reset_timestamp = datetime.now() + timedelta(seconds=cmd.time_to_show_in_seconds)
        self.last_shown_image_record = record
        yield ImageCommand(record.path)
        yield Confirmation(True).as_confirmation_for(cmd)

    @message_handler
    def on_timer(self, tick: TickEvent):
        if self.reset_timestamp is None:
            return
        if datetime.now() < self.reset_timestamp:
            return
        self.reset_timestamp = None
        yield ImageCommand(self.last_base_image_record.path)
        self.last_shown_image_record = self.last_base_image_record


_empty_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'
