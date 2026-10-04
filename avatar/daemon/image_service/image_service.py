import random
from typing import Union
from ..common import IMessage, State, TickEvent, ChatCommand, message_handler, ImageCommand, Confirmation, AvatarService, InitializationEvent
from .image_record import ImageRecord, VariantRecord
from .image_library_loader import ImageLibraryLoader
from ...app import AvatarApi
from foundation_kaia.marshalling import Storage
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
                 ):
        self.state = state
        self.api = api
        self.last_base_image_record: ImageRecord|None = None
        self.last_shown_image_record: ImageRecord|VariantRecord|None = None
        self.empty_image_uploaded: bool = False
        self.loader: ImageLibraryLoader|None = None
        self.current_records: list[ImageRecord] = []
        self.shown_this_round: set[str] = set()
        self.reset_timestamp: datetime|None = None

    @message_handler
    def on_initialize(self, message: InitializationEvent) -> None:
        self.loader = ImageLibraryLoader(
            Storage(self.resources_folder),
            self.resources_folder,
            ImageService.DESCRIPTION_SUFFIX,
        )

    def requires_brainbox(self):
        return False

    def _get_image_command(self, message: IMessage):
        if self.api is not None:
            self.api.cache.upload(self.last_base_image_record.file_id, self.last_base_image_record.get_content())
        return ImageCommand(
            self.last_base_image_record.file_id,
            self.last_base_image_record.tags,
        ).as_propagation_confirmation_to(message)

    def _get_empty_image(self, message: IMessage):
        if self.api is not None and not self.empty_image_uploaded:
            self.api.cache.upload('empty_image.png', _empty_image)
        return ImageCommand('empty_image.png').as_propagation_confirmation_to(message)

    def _pick_next(self) -> ImageRecord|None:
        feedback = self.loader.feedback_storage.load()
        available = []
        for requested in self.current_records:
            record = self.loader.get_record(requested.file_id)
            if record is None:
                continue
            if feedback.get(record.file_id, 'bad') != 0:
                continue
            available.append(record)
        if len(available) == 0:
            return None
        unshown = [r for r in available if r.file_id not in self.shown_this_round]
        pool = unshown if len(unshown) > 0 else available
        record = random.choice(pool)
        self.shown_this_round.add(record.file_id)
        return record

    def _show(self, message: IMessage) -> ImageCommand:
        record = self._pick_next()
        if record is None:
            self.last_shown_image_record = None
            return self._get_empty_image(message)
        self.last_base_image_record = record
        self.last_shown_image_record = record
        self.loader.feedback_storage.append(record.file_id, {'seen': 1})
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
        self.loader.feedback_storage.append(self.last_shown_image_record.file_id, {message.feedback: 1})
        if self.last_shown_image_record.file_id != self.last_base_image_record.file_id:
            key = '_'.join(['variant', self.last_shown_image_record.variant_type, message.feedback])
            self.loader.feedback_storage.append(self.last_base_image_record.file_id, {key: 1})
        return message.confirm_this()

    @message_handler
    def get_current_image_description(self, message: ImageDescriptionCommand) -> Union[Confirmation, ChatCommand]:
        if self.last_base_image_record is None:
            return message.error_on_this("No description")
        tags = ", ".join([f'{k}={v}' for k, v in self.last_base_image_record.tags.items() if v is not None])
        return ChatCommand(str(tags), ChatCommand.MessageType.system)

    @message_handler
    def on_variant_request(self, cmd: ImageVariantRequest):
        if self.last_base_image_record is None:
            yield Confirmation(False).as_confirmation_for(cmd)
            return

        self.loader.feedback_storage.append(self.last_base_image_record.file_id, {f'variant_requested_{cmd.variant_type}': 1})

        feedback = self.loader.feedback_storage.load()
        records = [
            r for r in self.loader.get_variants(self.last_base_image_record.file_id, cmd.variant_type)
            if feedback.get(r.file_id, 'bad') == 0
        ]

        if len(records) == 0:
            yield Confirmation(False).as_confirmation_for(cmd)
            return

        record: VariantRecord = random.choice(records)
        self.api.cache.upload(record.file_id, record.get_content())
        if cmd.time_to_show_in_seconds is not None:
            self.reset_timestamp = datetime.now() + timedelta(seconds=cmd.time_to_show_in_seconds)
        self.last_shown_image_record = record
        yield ImageCommand(record.file_id)
        yield Confirmation(True).as_confirmation_for(cmd)

    @message_handler
    def on_timer(self, tick: TickEvent):
        if self.reset_timestamp is None:
            return
        if datetime.now() < self.reset_timestamp:
            return
        self.reset_timestamp = None
        yield ImageCommand(self.last_base_image_record.file_id)
        self.last_shown_image_record = self.last_base_image_record


_empty_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'
