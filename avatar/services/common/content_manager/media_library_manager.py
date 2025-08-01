from .content_manager import ContentManager, IContentStrategy, ITagMatcher
from pathlib import Path
from brainbox import MediaLibrary
from .data_providers import MediaLibraryDataProvider


class MediaLibraryManager(ContentManager[MediaLibrary.Record]):
    def __init__(self,
                 media_library: str|Path|MediaLibrary,
                 feedback_file_path: Path|None = None,
                 strategy: IContentStrategy | None = None,
                 ):
        super().__init__(
            MediaLibraryDataProvider(media_library),
            feedback_file_path,
            strategy,
        )