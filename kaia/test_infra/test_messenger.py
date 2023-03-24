from apscheduler.schedulers.background import BackgroundScheduler
from unittest import TestCase
from kaia.infra import SqlMessenger, SearchOptions, Loc
import time
import threading
import multiprocessing


class Reader:
    def __init__(self, conn: SqlMessenger):
        self.conn = conn

    def make(self):
        try:
            tasks = self.conn.read(SearchOptions(open=True))
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
    def test_simple_scenario(self):
        cc = SqlMessenger()
        cc.add('test', dict(arg=1))
        tasks = cc.read()
        self.assertEqual(1, len(tasks))
        self.assertEqual('test',tasks[0].type)
        self.assertTrue(tasks[0].open)
        self.assertDictEqual(dict(arg=1), tasks[0].payload)
        cc.close(tasks[0].id, dict(res=2))
        tasks1 = cc.read()
        self.assertEqual(1, len(tasks1))
        self.assertEqual('test', tasks1[0].type)
        self.assertFalse(tasks1[0].open)
        self.assertDictEqual(dict(res=2), tasks1[0].result)

    def test_in_file(self):
        path = Loc.temp_folder/'test_db.db'
        cc = SqlMessenger(path)
        cc.add('x', None)
        self.assertEqual(1, len(cc.read()))
        cc = SqlMessenger(path)
        self.assertEqual(0, len(cc.read()))


    def test_in_file_memory(self):
        path = '/dev/shm/test_bro_db'
        cc = SqlMessenger(path)
        cc.add('x', None)
        self.assertEqual(1, len(cc.read()))
        cc = SqlMessenger(path)
        self.assertEqual(0, len(cc.read()))


    def test_filtration(self):
        cc = SqlMessenger()
        id1 = cc.add('test', '1')
        id2 = cc.add('test', '2')
        id3 = cc.add('test1',None)
        cc.close(id1,None)
        result = cc.read(SearchOptions(type='test', open=True))
        self.assertEqual(1, len(result))
        self.assertEqual(id2, result[0].id)
        result = cc.read(SearchOptions(open = False))
        self.assertEqual(1, len(result))
        self.assertEqual(id1, result[0].id)


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
        cc = SqlMessenger('/dev/shm/test_bro_db_1')
        process = multiprocessing.Process(target=Writer(cc).make)
        process.start()
        time.sleep(0.1)
        self.assertEqual(1, len(cc.read()))
        if process.is_alive():
            process.kill()


    def test_multiprocessing_works_with_file(self):
        cc = SqlMessenger(Loc.temp_folder/'test_bro_db_1')
        process = multiprocessing.Process(target=Writer(cc).make)
        process.start()
        time.sleep(0.1)
        self.assertEqual(1, len(cc.read()))
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
        cc = SqlMessenger('/dev/shm/test_bro_db_2')
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




