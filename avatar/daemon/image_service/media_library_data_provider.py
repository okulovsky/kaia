from pathlib import Path
from ..common.content_manager import IDataProvider
from .media_library import MediaLibrary


class MediaLibraryDataProvider(IDataProvider):
    def __init__(self, media_library: Path|str|MediaLibrary):
        if isinstance(media_library, MediaLibrary):
            self.media_library = media_library
        else:
            self.media_library = MediaLibrary(Path(media_library))

    def get_records(self) -> list[IDataProvider.Record]:
        return [IDataProvider.Record(r.path, r.tags, r) for r in self.media_library.records]
