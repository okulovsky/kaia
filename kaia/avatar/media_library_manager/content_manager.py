import copy
from typing import *
import pandas as pd
from .strategies import IContentStrategy
from .feedback_provider import InMemoryFeedbackProvider, FileFeedbackProvider
from pathlib import Path
from .tag_matcher import ITagMatcherFactory, ExactTagMatcher
from .data_providers import TRecord, IDataProvider, MediaLibraryDataProvider
from yo_fluq import Query


class ContentManager(Generic[TRecord]):
    def __init__(self,
                 strategy: IContentStrategy,
                 data_provider: IDataProvider,
                 feedback_file_path: Path|None = None,
                 tag_matcher_factory: ITagMatcherFactory = ExactTagMatcher.Factory1to1()
                 ):
        self.strategy = strategy
        self.data_provider =  data_provider
        if feedback_file_path is None:
            self.feedback_provider = InMemoryFeedbackProvider()
        else:
            self.feedback_provider = FileFeedbackProvider(feedback_file_path)
        self.tag_matcher_factory = tag_matcher_factory

    def find_content(self, state: dict[str, str], additional_required_tags: None|dict[str, str] = None) -> TRecord:
        records = self.data_provider.get_records()
        tag_matcher = self.tag_matcher_factory.prepare(state)
        filtered_records = [record for record in records if tag_matcher.match(record.tags, additional_required_tags)]
        feedback = self.feedback_provider.load_feedback()
        all_feedback_keys = set(key for fb in feedback.values() for key in fb)

        rows = []
        id_to_original = {}
        for record in filtered_records:
            row = copy.copy(record.tags)
            row['filename'] = record.filename
            for tag in all_feedback_keys:
                row['feedback_'+tag] = feedback.get(record.filename,{}).get(tag, 0)
            rows.append(row)
            id_to_original[record.filename] = record.original_record
        df = pd.DataFrame(rows)
        choosen_id = self.strategy.choose_filename(df)
        if choosen_id is None:
            return None
        return id_to_original[choosen_id]


    def get_content(self, state: dict[str,str], additional_required_tags: None|dict[str, str] = None) -> TRecord:
        content = self.find_content(state, additional_required_tags)
        if content is None:
            raise ValueError("No content can be found")
        return content

    def get_content_by_id(self, file_id) -> 'TRecord':
        return Query.en(self.data_provider.get_records()).where(lambda z: z.filename == file_id).single().original_record


    def feedback(self, last_file_id: str, feedback: str) -> None:
        self.feedback_provider.append_feedback(last_file_id, {feedback:1})

