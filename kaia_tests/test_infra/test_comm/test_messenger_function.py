from unittest import TestCase
from kaia.infra.comm import Sql, MessengerQuery
from kaia.infra import Loc
import os

class SqlMessengerTestCase(TestCase):
    def test_one_message(self):
        cc = Sql.memory().messenger()
        id = cc.add(None,'is_alive')
        self.assertEqual(id, MessengerQuery(id=id).query_single(cc).id)

    def test_simple_scenario(self):
        cc = Sql.memory().messenger()
        cc.add(dict(arg=1), 'test')
        tasks = cc.read()
        self.assertEqual(1, len(tasks))
        self.assertEqual('test',tasks[0].tags[0])
        self.assertTrue(tasks[0].open)
        self.assertDictEqual(dict(arg=1), tasks[0].payload)
        cc.close(tasks[0].id, dict(res=2))
        tasks1 = cc.read()
        self.assertEqual(1, len(tasks1))
        self.assertEqual('test', tasks1[0].tags[0])
        self.assertFalse(tasks1[0].open)
        self.assertDictEqual(dict(res=2), tasks1[0].result)

    def test_multi_tags(self):
        cc = Sql.memory().messenger()
        id1 = cc.add(dict(a=1), '1', '10')
        id2 = cc.add(dict(a=2), '1', '20')
        id3 = cc.add(dict(a=3), '2', '10')
        id4 = cc.add(dict(a=3), '2', '20')
        tasks = MessengerQuery(tags=['1']).query(cc)
        self.assertListEqual([id1, id2], [z.id for z in tasks])
        tasks = MessengerQuery(tags=[None, '20']).query(cc)
        self.assertListEqual([id2, id4], [z.id for z in tasks])

    def test_multi_multi_tags(self):
        cc = Sql.memory().messenger()
        id1 = cc.add(dict(a=1), '1', '10')
        id2 = cc.add(dict(a=2), '1', '20')
        id3 = cc.add(dict(a=3), '1', '30')
        id4 = cc.add(dict(a=1), '1', '10')
        id5 = cc.add(dict(a=2), '1', '20')
        id6 = cc.add(dict(a=3), '2', '30')
        tasks = MessengerQuery(tags=['1', ['10','20']]).query(cc)
        self.assertEqual([id1, id2, id4, id5], [z.id for z in tasks])

        tasks = MessengerQuery(tags=[None, ['20']]).query(cc)
        self.assertEqual([id2, id5], [z.id for z in tasks])

    def test_in_file(self):
        path = Loc.temp_folder/'tests/messenger/test_db.db'
        os.makedirs(path.parent, exist_ok=True)
        cc = Sql.file(path, True).messenger()
        cc.add(None, 'x')
        self.assertEqual(1, len(cc.read()))
        cc = Sql.file(path, True).messenger()
        self.assertEqual(0, len(cc.read()))


    def test_in_file_memory(self):
        path = '/dev/shm/test_bro_db'
        cc = Sql.file(path, True).messenger()
        cc.add(None, 'x')
        self.assertEqual(1, len(cc.read()))
        cc = Sql.file(path, True).messenger()
        self.assertEqual(0, len(cc.read()))


    def test_filtration(self):
        cc = Sql.memory().messenger()
        id1 = cc.add('1', 'test')
        id2 = cc.add('2', 'test')
        id3 = cc.add(None, 'test1')
        cc.close(id1,None)
        result = cc.read(MessengerQuery(tags='test', open=True))
        self.assertEqual(1, len(result))
        self.assertEqual(id2, result[0].id)
        result = cc.read(MessengerQuery(open = False))
        self.assertEqual(1, len(result))
        self.assertEqual(id1, result[0].id)
