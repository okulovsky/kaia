from typing import *
import os.path
from abc import ABC, abstractmethod

import numpy.random
from ...eaglesong.core import Image
from ...brainbox import MediaLibrary
from pathlib import Path
from kaia.infra import FileIO
from yo_fluq import Query


class IImageService:
    @abstractmethod
    def get_image(self, tags: dict[str, str]) -> Image:
        pass

    @abstractmethod
    def report(self, id: str) -> None:
        pass



class SimpleImageService(IImageService):
    def __init__(self,
                 media_library_path: Path,
                 stats_file: Path,
                 randomize: bool = True
                 ):
        self.media_library = MediaLibrary.read(media_library_path)
        self.stats_file = stats_file
        self.randomize = randomize


    def load_stats_file(self):
        if not os.path.isfile(self.stats_file):
            return dict(seen={}, feedback={})
        return FileIO.read_json(self.stats_file)

    def save_stats_file(self, stats):
        FileIO.write_json(stats, self.stats_file)


    def filter_records_by_exposure(self, records: Iterable[MediaLibrary.Record]):
        stats = self.load_stats_file()
        record_to_count = {}
        for record in records:
            if record.filename in stats['feedback']:
                continue
            if record.filename in stats['seen']:
                record_to_count[record.filename] = stats['seen'][record.filename]
            else:
                record_to_count[record.filename] = 0
        if len(record_to_count) == 0:
            return stats, []
        min_seen = min(record_to_count.values())
        good_records = [record for record in records if record_to_count.get(record.filename,-1) == min_seen]
        return stats, good_records


    def filter_records_by_tags(self, records: Iterable[MediaLibrary.Record], tags: dict[str, str]):
        good_records = []
        for record in records:
            is_ok = True
            for key, value in tags.items():
                if key not in record.tags:
                    is_ok = False
                    break
                if value != record.tags[key]:
                    is_ok = False
                    break
            if is_ok:
                good_records.append(record)
        return good_records

    def get_image(self, tags: dict[str, str]) -> Optional[Image]:
        records = self.media_library.records
        records = self.filter_records_by_tags(records, tags)
        stats, records = self.filter_records_by_exposure(records)
        if len(records) == 0:
            return None
        if self.randomize:
            record_to_take = records[numpy.random.randint(len(records))]
        else:
            min_name = min(record.filename for record in records)
            record_to_take = [record for record in records if record.filename == min_name][0]
        content = record_to_take.get_content()
        image = Image(content, None, record_to_take.filename)
        if record_to_take.filename not in stats['seen']:
            stats['seen'][record_to_take.filename] = 0
        stats['seen'][record_to_take.filename] += 1
        self.save_stats_file(stats)
        return image

    def report(self, id: str) -> None:
        stats = self.load_stats_file()
        stats['feedback'][id] = 'bad'
        self.save_stats_file(stats)






