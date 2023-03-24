from datetime import datetime
import zipfile
from pathlib import Path
from yo_fluq_ds import *


class Storage:
    def __init__(self,
                 folder: Path,
                 buffer_length: int,
                 buffer_keep_after_flush: int
                 ):
        self.folder = folder
        self.current = self.folder/'current.jsonlines'
        self.buffer = []
        self.file_handler = None
        self.buffer_length = buffer_length
        self.buffer_keep_after_flush = buffer_keep_after_flush

        self._initialize_at_startup()


    def _initialize_at_startup(self):
        if not os.path.isdir(str(self.folder)):
            os.makedirs(str(self.folder))
        if os.path.isfile(str(self.current)):
            self.buffer =  Query.file.text(self.current).select(jsonpickle.loads).to_list()

        self.file_handler = open(str(self.current), 'a')


    def _archive(self):
        self.file_handler.close()
        archive_id = self.get_max_archive_id()+1
        fname = self.folder/(f'archive.{archive_id}.zip')
        with zipfile.ZipFile(fname,'w',zipfile.ZIP_DEFLATED) as file:
            to_write = self.buffer[:-self.buffer_keep_after_flush]
            data_to_write = [c['data'] for c in to_write]
            timestamps_to_write = [c['timestamp'] for c in to_write]
            file.writestr('length', jsonpickle.dumps(len(to_write)))
            file.writestr('timestamps', jsonpickle.dumps(timestamps_to_write))
            file.writestr('data', jsonpickle.dumps(data_to_write))
        self.buffer = self.buffer[-self.buffer_keep_after_flush:]
        Query.en(self.buffer).select(jsonpickle.dumps).to_text_file(self.current)
        self.file_handler = open(str(self.current), 'a')

    def get_max_archive_id(self):
        return Query.folder(self.folder,'*.zip').select(lambda z: int(z.name.split('.')[1])).max(default=-1)

    def get_archive_file_path(self, archive_index):
        return self.folder / (f'archive.{archive_index}.zip')

    def store(self, obj, timestamp = None):
        if timestamp is None:
            timestamp = datetime.now()
        stored = dict(timestamp=timestamp, data=obj)
        self.buffer.append(stored)
        self.file_handler.write(jsonpickle.dumps(stored)+'\n')
        self.file_handler.flush()
        if len(self.buffer)>=self.buffer_length:
            self._archive()

    def get_reader(self) -> 'StorageReader':
        return StorageReader(self)


class StorageReader:
    def __init__(self, storage: Storage):
        self.storage = storage


    def _read_from_archive(self, archive_id, *terms):
        result = {}
        with zipfile.ZipFile(self.storage.get_archive_file_path(archive_id), 'r') as file:
            for t in terms:
                result[t] = jsonpickle.loads(file.read(t))
        return result

    def _load_counts_and_stamps(self):
        max_id = self.storage.get_max_archive_id()
        yield (None, len(self.storage.buffer), [c['timestamp'] for c in self.storage.buffer], max_id)
        for i in range(max_id,-1,-1):
            data = self._read_from_archive(i, 'length', 'timestamps')
            yield(i, data['length'], data['timestamps'], max_id)

    class _Start:
        def __init__(self, first_offset, start_from_archive_index, max_archive_index, total_count):
            self.first_offset = first_offset
            self.start_from_archive_index = start_from_archive_index
            self.max_archive_index = max_archive_index
            self.total_count = total_count

    def _find_archive_and_offset_for_count(self, count):
        if count == 0:
            return StorageReader._Start(None, None, None, count)
        max_id = None
        for arch_id, buf_count, _, max_id in self._load_counts_and_stamps():
            if count<=buf_count:
                return StorageReader._Start(-count, arch_id, max_id, count)
            count -= buf_count
        return StorageReader._Start(None, 0, max_id, count)

    def _find_archive_and_offset_for_time(self, start):
        max_id = None
        total_count = 0
        for arch_id, _, timestamps, max_id in self._load_counts_and_stamps():
            if timestamps[-1] < start:
                if arch_id is None:
                    return StorageReader._Start(None, None, None, 0)
                if arch_id == max_id:
                    return StorageReader._Start(None, None, None, total_count)
                return StorageReader._Start(None, arch_id+1, max_id, total_count)
            if timestamps[0] > start:
                total_count+=len(timestamps)
                continue
            for i in reversed(range(len(timestamps))):
                if timestamps[i] < start:
                    return StorageReader._Start(i+1, arch_id, max_id, total_count+len(timestamps)-i-1)
        return StorageReader._Start(None, 0, max_id, total_count)

    def _load_blocks_iter(self, start: 'StorageReader._Start'):
        if start.total_count!=0:
            first = True
            if start.start_from_archive_index is not None and start.max_archive_index is not None:
                for i in range(start.start_from_archive_index, start.max_archive_index+1, 1):
                    data = self._read_from_archive(i, 'data')['data']
                    if first and start.first_offset is not None:
                        data = data[start.first_offset:]
                        first = False
                    yield data
            data = [c['data'] for c in self.storage.buffer]
            if first and start.first_offset is not None:
                data = data[start.first_offset:]
            yield data

    def read_data_from_archive(self, archive_index):
        return self._read_from_archive(archive_index, 'data')['data']

    def read_records(self, count):
        start = self._find_archive_and_offset_for_count(count)
        en = Query.en(self._load_blocks_iter(start)).select_many(lambda z: z)
        return Queryable(en, start.total_count)

    def read_records_after_timestamp(self, timestamp):
        start = self._find_archive_and_offset_for_time(timestamp)
        en = Query.en(self._load_blocks_iter(start)).select_many(lambda z: z)
        return Queryable(en, start.total_count)









