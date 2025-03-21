from typing import *
from dataclasses import dataclass
from .strategies import IContentStrategy
from .feedback_provider import InMemoryFeedbackProvider, FileFeedbackProvider
from pathlib import Path
from brainbox import MediaLibrary
from .tag_matcher import ITagMatcherFactory, ExactTagMatcher

class MediaLibraryManager:
    @dataclass
    class Record:
        file_id: str
        content: Any
        original_record: MediaLibrary.Record

    def __init__(self,
                 strategy: IContentStrategy,
                 media_library: Path|MediaLibrary,
                 feedback_file_path: Path|None = None,
                 tag_matcher_factory: ITagMatcherFactory = ExactTagMatcher.Factory1to1()
                 ):
        self.strategy = strategy
        if isinstance(media_library, MediaLibrary):
            self.media_library = media_library
        else:
            self.media_library = MediaLibrary.read(media_library)
        if feedback_file_path is None:
            self.feedback_provider = InMemoryFeedbackProvider()
        else:
            self.feedback_provider = FileFeedbackProvider(feedback_file_path)
        self.tag_matcher_factory = tag_matcher_factory

    def find_content(self, state: dict[str, str], additional_required_tags: None|dict[str, str] = None) -> Optional['MediaLibraryManager.Record']:
        ml = self.media_library
        tag_matcher = self.tag_matcher_factory.prepare(state)
        filtered_ids = [record.filename for record in ml.records if tag_matcher.match(record.tags, additional_required_tags)]
        ml = ml.limit_to(filtered_ids)
        ml = self.feedback_provider.add_feedback_to_media_library(ml)
        choosen_id = self.strategy.choose_filename(ml)
        if choosen_id is None:
            return None
        return MediaLibraryManager.Record(choosen_id, ml.mapping[choosen_id].get_content(), ml.mapping[choosen_id])


    def get_content(self, state: dict[str,str], additional_required_tags: None|dict[str, str] = None) -> 'MediaLibraryManager.Record':
        content = self.find_content(state, additional_required_tags)
        if content is None:
            raise ValueError("No content can be found")
        return content

    def get_content_by_id(self, file_id) -> 'MediaLibraryManager.Record':
        record = self.media_library[file_id]
        return MediaLibraryManager.Record(record.filename, record.get_content(), record)


    def feedback(self, last_file_id: str, feedback: str) -> None:
        self.feedback_provider.append_feedback(last_file_id, {feedback:1})






