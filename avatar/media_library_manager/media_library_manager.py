from .content_manager import ContentManager, IContentStrategy, ITagMatcherFactory, ExactTagMatcher
from pathlib import Path
from brainbox import MediaLibrary
from .data_providers import MediaLibraryDataProvider


class MediaLibraryManager(ContentManager[MediaLibrary.Record]):
    def __init__(self,
                 strategy: IContentStrategy,
                 media_library: str|Path|MediaLibrary,
                 feedback_file_path: Path|None = None,
                 tag_matcher_factory: ITagMatcherFactory = ExactTagMatcher.Factory1to1()
                 ):
        super().__init__(
            strategy,
            MediaLibraryDataProvider(media_library),
            feedback_file_path,
            tag_matcher_factory
        )