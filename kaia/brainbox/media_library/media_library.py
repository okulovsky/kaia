from typing import *
from dataclasses import dataclass,field
from pathlib import Path
import shutil
import os
import zipfile
from datetime import datetime
import pickle
from ...infra import FileIO
from copy import deepcopy

import pandas as pd
from yo_fluq import Queryable
from copy import copy

DESCRIPTION_FILE_NAME = 'description.pkl'
ERRORS_FILE_NAME = 'errors.pkl'


class MediaLibrary:
    @dataclass(frozen=True)
    class Record:
        filename: str
        holder_location: Path|None
        timestamp: None|datetime = None
        job_id: None|str = None
        tags: Dict[str, Any] = field(default_factory=dict)
        inline_content: Any = None

        def get_full_path(self):
            if self.packed:
                raise ValueError('This is a packed file, no full path exists')
            return self.holder_location/self.filename

        def change_folder(self, host_folder):
            return MediaLibrary.Record(self.filename, host_folder, self.timestamp, self.job_id, self.tags)

        @property
        def unpacked(self):
            return self.inline_content is None and self.holder_location.is_dir()

        @property
        def packed(self):
            return self.inline_content is None and self.holder_location.is_file()

        @property
        def inline(self):
            return self.inline_content is not None

        def get_content(self, zip_file = None):
            if self.inline:
                return self.inline_content
            elif self.unpacked:
                with open(self.holder_location / self.filename, 'rb') as stream:
                    return stream.read()
            else:
                if zip_file is not None:
                    return zip_file.read(self.filename)
                with zipfile.ZipFile(self.holder_location, 'r', zipfile.ZIP_DEFLATED) as zp:
                    return zp.read(self.filename)

    def __init__(self,
                 records: Tuple['MediaLibrary.Record', ...] = (),
                 errors: Tuple[str,...] = (),
                 info: Any = None
                 ):
        self._records = tuple(records)
        self._errors = tuple(errors)
        self._mapping = {r.filename: r for r in self.records}
        self._info = info

    @property
    def records(self) -> Tuple[Record,...]:
        return self._records

    @property
    def errors(self) -> Tuple[str,...]:
        return self._errors

    @property
    def mapping(self) -> Mapping[str, Record]:
        return self._mapping

    @property
    def info(self) -> Any:
        return self._info

    def clone(self) -> 'MediaLibrary':
        return deepcopy(self)

    def limit_to(self, ids: Iterable[str]):
        ids = set(ids)
        return MediaLibrary(
            tuple(deepcopy(z) for z in self.records if z.filename in ids),
            (),
            self.info
        )


    def __getitem__(self, item: str) -> 'MediaLibrary.Record':
        return self.mapping[item]

    def __iter__(self):
        yield from self.records

    def enumerate_content(self) -> Iterable[Tuple['MediaLibrary.Record',bytes]]:
        non_packed = []
        packed = {}
        for record in self.records:
            if record.packed:
                if record.holder_location not in packed:
                    packed[record.holder_location] = []
                packed[record.holder_location].append(record)
            else:
                non_packed.append(record)
        for record in non_packed:
            yield (record, record.get_content())
        for zp_location, records in packed.items():
            with zipfile.ZipFile(zp_location, 'r', zipfile.ZIP_DEFLATED) as zp:
                for record in records:
                    yield (record, record.get_content(zp))

    def to_df(self):
        df = pd.DataFrame([r.tags for r in self.records])
        for field in ['filename','timestamp','job_id']:
            df[field] = [getattr(r, field) for r in self.records]
        return df


    def save(self, location: Path, with_progress_bar: bool = False):
        with zipfile.ZipFile(location, 'w', zipfile.ZIP_DEFLATED) as zp:
            source = Queryable(self.enumerate_content(), len(self.records))

            records = {}
            for record, content in source:
                if not record.inline:
                    zp.writestr(record.filename, content)
                dct = copy(record.__dict__)
                del dct['holder_location']
                records[record.filename] = dct

            zp.writestr(DESCRIPTION_FILE_NAME, pickle.dumps(records))
            zp.writestr(ERRORS_FILE_NAME, pickle.dumps(list(self.errors)))



    def unzip(self, folder: Path, with_progress_bar: bool = False):
        if os.path.isfile(folder):
            raise ValueError(f'{folder} is a file')
        elif os.path.isdir(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)

        source = Queryable(self.enumerate_content(), len(self.records))

        records = []
        for record, content in source:
            if not record.inline:
                with open(folder/record.filename, 'wb') as stream:
                    stream.write(content)
            records.append(record.change_folder(folder))

        return MediaLibrary(tuple(records), self.errors)




    def merge(self, another: 'MediaLibrary') -> 'MediaLibrary':
        return MediaLibrary(
            self.records + another.records,
            self.errors + another.errors
        )


    @staticmethod
    def _load_zip(zip_file: Path, host_folder: Optional[Path]) -> 'MediaLibrary':
        with zipfile.ZipFile(zip_file, 'r', zipfile.ZIP_DEFLATED) as zp:
            errors = pickle.loads(zp.read(ERRORS_FILE_NAME))
            result = []
            desc = pickle.loads(zp.read(DESCRIPTION_FILE_NAME))
            name_list = zp.namelist()
            for key, value in desc.items():
                if 'inline_content' not in value:
                    value['inline_content'] = None #compatibility assignment
                if value['inline_content'] is None and key not in name_list:
                    raise ValueError(f'File {key} is listed in {DESCRIPTION_FILE_NAME}, but is absent from archive file {zip_file}')

                if value['inline_content'] is not None:
                    location = None
                elif host_folder is None:
                    location = zip_file
                else:
                    location = host_folder

                item = MediaLibrary.Record(holder_location=location, **value)
                result.append(item)
        return MediaLibrary(tuple(result), tuple(errors))

    @staticmethod
    def _load_zips(zip_files: Iterable[Path], host_folder: Optional[Path]) -> 'MediaLibrary':
        result = None
        for zip_file in zip_files:
            addition = MediaLibrary._load_zip(zip_file, host_folder)
            if result is None:
                result = addition
            else:
                result = result.merge(addition)
        return result

    @staticmethod
    def read(*zip_files: Path) -> 'MediaLibrary':
        zip_files = [Path(p) for p in zip_files]
        return MediaLibrary._load_zips(zip_files, None)


    @staticmethod
    def generate(path: Path, tags_array: Dict[str,Dict[str,Any]]):
        folder = path.parent/("tmp_"+path.name)
        os.makedirs(folder, exist_ok=True)
        records = []
        for fname, tags in tags_array.items():
            record = MediaLibrary.Record(
                filename = fname,
                holder_location=folder,
                timestamp=datetime.now(),
                job_id='',
                tags = tags,
                inline_content=None
            )
            records.append(record)
            FileIO.write_json(tags, folder/fname)
        library = MediaLibrary(tuple(records))
        library.save(path)
        shutil.rmtree(folder)




