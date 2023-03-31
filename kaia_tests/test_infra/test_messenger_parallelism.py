import os

from apscheduler.schedulers.background import BackgroundScheduler
from unittest import TestCase
from kaia.infra import SqlMessenger, MessengerQuery, Loc
import time
import threading
import multiprocessing


class Reader:
    def __init__(self, conn: SqlMessenger):
        self.conn = conn

    def make(self):
        try:
            tasks = self.conn.read(MessengerQuery(open=True))
            if len(tasks) > 0:
                self.conn.close(tasks[0].id, None)
        except:
            pass


class Writer:
    def __init__(self, conn: SqlMessenger, cnt = 1):
        self.conn = conn
        self.cnt = cnt

    def make(self):
        for i in range(self.cnt):
            self.conn.add('x','x')


class SqlLiteTestCase(TestCase):
    def test_writing_in_bg_scheduler(self):
        cc = SqlMessenger()
        scheduler = BackgroundScheduler()
        scheduler.add_job(Writer(cc).make, trigger='interval', seconds=0.2)
        scheduler.start()
        lens = []
        for i in range(10):
            lens.append(len(cc.read()))
            time.sleep(0.1)
        scheduler.shutdown()

        for i in range(len(lens) - 1):
            self.assertGreaterEqual(lens[i + 1], lens[i])
        self.assertGreaterEqual(lens[-1], lens[0])

    def test_writing_from_thread(self):
        cc = SqlMessenger()
        thread = threading.Thread(target = Writer(cc).make)
        thread.setDaemon(True)
        thread.start()
        time.sleep(0.1)
        self.assertEqual(1, len(cc.read()))

    def test_in_memory_does_not_work_with_multiprocessing(self):
        cc = SqlMessenger()
        process = multiprocessing.Process(target=Writer(cc).make)
        process.start()
        time.sleep(0.1)
        self.assertEqual(0, len(cc.read()))
        if process.is_alive():
            process.kill()

    def test_multiprocessing_works_with_mnt(self):
        cc = SqlMessenger('/dev/shm/test_bro_db_1', True)
        process = multiprocessing.Process(target=Writer(cc).make)
        process.start()
        time.sleep(0.1)
        self.assertEqual(1, len(cc.read()))
        if process.is_alive():
            process.kill()


    def test_multiprocessing_works_with_file(self):
        location = Loc.temp_folder/'tests/messenger/test_bro_db_1'
        os.makedirs(location.parent, exist_ok=True)
        cc = SqlMessenger(location, True)
        process = multiprocessing.Process(target=Writer(cc).make)
        process.start()
        time.sleep(0.1)
        self.assertEqual(1, len(cc.read()))
        if process.is_alive():
            process.kill()

    def test_multiprocessing_word_with_file_2(self):
        location = Loc.temp_folder / 'tests/messenger/test_bro_db_2'
        os.makedirs(location.parent, exist_ok=True)
        cc = SqlMessenger(location, True)
        process = multiprocessing.Process(target = Reader(cc).make)
        process.start()
        time.sleep(0.1)
        cc.add('message')
        time.sleep(0.1)
        q = cc.read()
        print(q[0].open)
        if process.is_alive():
            process.kill()


    def test_stress_threads(self):
        N = 10
        CNT=1000
        threads = []
        cc = SqlMessenger()
        for i in range(N):
            t = threading.Thread(target = Writer(cc,CNT).make)
            t.setDaemon(True)
            threads.append(t)
        for t in threads:
            t.start()
        time.sleep(1)
        r = len(cc.read())
        self.assertEqual(N*CNT, r)

    def test_stress_processes(self):
        N = 10
        CNT=100
        threads = []
        cc = SqlMessenger('/dev/shm/test_bro_db_2', True)
        for i in range(N):
            t = multiprocessing.Process(target = Writer(cc,CNT).make)
            threads.append(t)
        for t in threads:
            t.start()
        time.sleep(2)
        for t in threads:
            t.kill()
        r = len(cc.read())
        self.assertEqual(N*CNT, r)




