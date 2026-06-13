from ..common.content_manager import ContentManager, IContentStrategy
from pathlib import Path
from .media_library import MediaLibrary
from .media_library_data_provider import MediaLibraryDataProvider


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