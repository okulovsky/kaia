from kaia.infra import Storage
from unittest import TestCase
from pathlib import Path
import shutil
from yo_fluq_ds import *
from datetime import datetime, timedelta

class TestStorage:
    def __init__(self, buffer_length=110, buffer_keep_after_flush=10):
        self.buffer_length = buffer_length
        self.buffer_keep_after_flush = buffer_keep_after_flush
        self.folder = Path(__file__).parent / 'temp'

    def __enter__(self):
        shutil.rmtree(self.folder, True)
        os.makedirs(self.folder)
        storage = Storage(self.folder, self.buffer_length, self.buffer_keep_after_flush)
        return storage

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.folder, True)
        pass


START_TIME = datetime(2020,1,1)

class StorageTestCase(TestCase):
    def send(self, s, count):
        for i in range(count):
            s.store(i, START_TIME+timedelta(seconds=i))


    def check(self, values_from, values_to, data):
        due_values = list(range(values_from, values_to))
        if len(data) == 0:
            self.assertEqual(0, values_to-values_from)
        if isinstance(data[0], int):
            self.assertListEqual(due_values, data)
            return
        self.assertListEqual(due_values, [c['data'] for c in data])
        due_timestamps = [START_TIME+timedelta(seconds=i) for i in due_values]
        self.assertListEqual(due_timestamps, [c['timestamp'] for c in data])


    def test_immediate_writing(self):
        with TestStorage() as s:
            s.store(datetime.now())
            self.assertEqual(1, Query.file.text(s.current).count())
            s.store({'a':1, 'b':2})
            self.assertEqual(2, Query.file.text(s.current).count())

    def test_doesnt_store_before_the_limit(self):
        with TestStorage() as s:
            self.send(s, 109)
            self.assertEqual(1, Query.folder(s.folder).count())

    def test_does_store_at_limit(self):
        with TestStorage() as s:
            self.send(s, 110)

            self.assertEqual(2, Query.folder(s.folder).count())
            self.assertEqual(s.buffer_keep_after_flush, len(s.buffer))

            self.check(100,110, s.buffer)
            stored_buffer = Query.file.text(s.current).select(jsonpickle.loads).to_list()
            self.check(100,110, stored_buffer)

            archive = s.get_reader().read_data_from_archive(0)
            self.check(0,100, archive)

            s1 = Storage(s.folder, 100, 10)
            self.check(100,110, s1.buffer)

    def test_several_archives(self):
        with TestStorage() as s:
            self.send(s, 250)
            files = Query.folder(s.folder).select(lambda z: z.name).order_by(lambda z: z).to_list()
            self.assertListEqual(['archive.0.zip', 'archive.1.zip', 'current.jsonlines'], files)
            self.check(200,250, s.buffer)
            self.check(0,100, s.get_reader().read_data_from_archive(0))
            self.check(100, 200, s.get_reader().read_data_from_archive(1))


    def check_reading_by_count(self, s, cnt, real_cnt = None):
        with self.subTest(f'{cnt} by count'):
            if real_cnt is None:
                real_cnt = cnt
            buffer = s.get_reader().read_records(cnt).to_list()
            self.assertListEqual(list(range(250-real_cnt,250)), buffer)

    def check_reading_by_time(self, s, cnt, real_cnt = None):
        with self.subTest(f'{cnt} by time'):
            if real_cnt is None:
                real_cnt = cnt
            time = START_TIME + timedelta(seconds=250 - cnt - 0.5)
            buffer = s.get_reader().read_records_after_timestamp(time)
            self.assertEqual(real_cnt, buffer.length)
            buffer = buffer.to_list()
            self.assertListEqual(list(range(250 - real_cnt, 250)), buffer)

    def test_reading(self):
        with TestStorage() as s:
            self.send(s, 250)
            for i in [0, 1, 2, 5, 49, 50, 51, 52, 100, 149, 150, 151]:
                self.check_reading_by_time(s, i)
                self.check_reading_by_count(s, i)
            self.check_reading_by_time(s, 300, 250)
            self.check_reading_by_count(s, 300, 250)







