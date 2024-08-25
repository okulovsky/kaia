from typing import *
from dataclasses import dataclass
from .strategies import IContentStrategy
from .feedback_provider import FeedbackProvider
from pathlib import Path
from kaia.brainbox import MediaLibrary
from .tag_matcher import ITagMatcherFactory, ExactTagMatcher

class MediaLibraryManager:
    @dataclass
    class Record:
        file_id: str
        content: Any

    def __init__(self,
                 strategy: IContentStrategy,
                 media_library_path: Path,
                 feedback_file_path: Path,
                 tag_matcher_factory: ITagMatcherFactory = ExactTagMatcher.Factory1to1()
                 ):
        self.strategy = strategy
        self.media_library = MediaLibrary.read(media_library_path)
        self.feedback_provider = FeedbackProvider(feedback_file_path)
        self.last_image_id: None | str = None
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
        self.last_image_id = choosen_id
        self.feedback_provider.append_feedback(self.last_image_id, dict(seen=1))
        return MediaLibraryManager.Record(choosen_id, ml.mapping[choosen_id].get_content())


    def get_content(self, state: dict[str,str], additional_required_tags: None|dict[str, str] = None) -> 'MediaLibraryManager.Record':
        content = self.find_content(state, additional_required_tags)
        if content is None:
            self.last_image_id = None
            raise ValueError("No content can be found")
        return content


    def feedback(self, feedback: str) -> None:
        if self.last_image_id is None:
            raise ValueError(f'No image was sent, so no feedback is going to be provided')
        self.feedback_provider.append_feedback(self.last_image_id, {feedback:1})






