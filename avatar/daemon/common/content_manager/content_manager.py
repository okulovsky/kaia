import copy
from typing import *
import pandas as pd
from .strategies import IContentStrategy, NewContentStrategy
from .feedback_provider import InMemoryFeedbackProvider, FileFeedbackProvider
from pathlib import Path
from .tag_matcher import ITagMatcher, TagMatcher
from .data_providers import TRecord, IDataProvider, MediaLibraryDataProvider
from yo_fluq import Query

class Matcher(Generic[TRecord]):
    def __init__(self, data_provider, feedback_provider, strategy):
        self.data_provider = data_provider
        self.feedback_provider = feedback_provider
        self.matchers: list[ITagMatcher] = []
        self.strategy = strategy

    def weak(self, tags: dict[str, Any]) -> 'Matcher[TRecord]':
        self.matchers.append(TagMatcher(False, tags))
        return self

    def strong(self, tags: dict[str, Any]) -> 'Matcher[TRecord]':
        self.matchers.append(TagMatcher(True, tags))
        return self

    def get_all_acceptable(self) -> list[TRecord]:
        records = self.data_provider.get_records()

        filtered_records = []
        for record in records:
            skip = False
            for matcher in self.matchers:
                if not matcher.match(record.tags):
                    skip = True
                    break
            if not skip:
                filtered_records.append(record)

        return filtered_records

    def find_content(self) -> TRecord|None:
        records = self.get_all_acceptable()

        feedback = self.feedback_provider.load_feedback()
        all_feedback_keys = set(key for fb in feedback.values() for key in fb)

        rows = []
        id_to_original = {}
        for record in records:
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

    def get_content(self) -> TRecord:
        content = self.find_content()
        if content is None:
            raise ValueError("No content can be found")
        return content



class ContentManager(Generic[TRecord]):
    def __init__(self,
                 data_provider: IDataProvider,
                 feedback_file_path: Path|None = None,
                 strategy: IContentStrategy|None = None
                 ):
        if strategy is None:
            strategy = NewContentStrategy(False)
        self.strategy = strategy
        self.data_provider = data_provider
        if feedback_file_path is None:
            self.feedback_provider = InMemoryFeedbackProvider()
        else:
            self.feedback_provider = FileFeedbackProvider(feedback_file_path)

    def get_content_by_id(self, file_id) -> 'TRecord':
        return Query.en(self.data_provider.get_records()).where(lambda z: z.filename == file_id).single().original_record


    def feedback(self, last_file_id: str, feedback: str) -> None:
        self.feedback_provider.append_feedback(last_file_id, {feedback:1})

    def match(self) -> Matcher[TRecord]:
        return Matcher(self.data_provider, self.feedback_provider, self.strategy)

