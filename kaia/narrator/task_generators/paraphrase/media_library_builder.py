from typing import *
from copy import copy
from kaia.brainbox import MediaLibrary
from uuid import uuid4
from datetime import datetime
from kaia.brainbox.deciders import Collector

class MediaLibraryBuilder:
    @staticmethod
    def build_media_library(reply_to_options: Callable[[str], Iterable[str]],
                            result):
        records = []
        errors = []
        for id, tags in result['tags'].items():
            reply = result[id]
            if not isinstance(reply, str):
                errors.append(f'Response for {id} was {reply}, str expected')
                continue
            for index, line in enumerate(reply_to_options(result[id])):
                clean_tags = copy(tags)
                clean_tags['option_index'] = index
                record = MediaLibrary.Record(
                    filename=str(uuid4()),
                    holder_location=None,
                    timestamp=datetime.now(),
                    job_id=None,
                    tags=clean_tags,
                    inline_content=line
                )
                records.append(record)
        return MediaLibrary(tuple(records), tuple(errors))

    @staticmethod
    def filter_existing_tasks(
            pack_builder: Collector.PackBuilder,
            ml: MediaLibrary
    ):
        new_records = []
        for record in pack_builder.records:
            keep = True
            for existing_record in ml.records:
                all_equal = True
                for k in record.tags:
                    if existing_record.tags[k] != record.tags[k]:
                        all_equal = False
                        break
                if all_equal:
                    keep = False
                    break
            if keep:
                new_records.append(record)
        return Collector.PackBuilder(new_records)
