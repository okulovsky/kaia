from kaia.bro.sandbox import SimpleSpace
from kaia.bro.core import BroAlgorithm, BroClient, DebugClientDataProvider, StorageClientDataProvider
from kaia.bro import amenities as am
from unittest import TestCase
from kaia.infra.comm import IMessenger, Sql, IStorage, FakeStorage, FakeMessenger
import pandas as pd

class AlgorithmTestCase(TestCase):
    def test_algorithm(self):
        def _algorithm(space: SimpleSpace):
            space.int_slot.current_value = space.int_slot.history.first_or_default(-1)+1
            space.string_slot.current_value = 'a' + str(space.int_slot.current_value)

        space = SimpleSpace()
        alg = BroAlgorithm(
            space,
            [_algorithm]
        )
        for i in range(5):
            res = alg.iterate(FakeStorage(), FakeMessenger())

        self.assertListEqual([4,3,2,1,0], space.int_slot.history.to_list())
        self.assertListEqual(['a4', 'a3', 'a2', 'a1', 'a0'], space.string_slot.history.to_list())

    def test_notification(self):
        def _algorithm(space: SimpleSpace):
            space.int_slot.current_value = space.int_slot.history.first_or_default(-1) + 1
            print(space.int_slot.current_value)
            space.string_slot.current_value = None if space.int_slot.current_value%3 != 0 else f'b{space.int_slot.current_value}'

        space = SimpleSpace()
        messenger = Sql.file().messenger()
        alg = BroAlgorithm(
            space,
            [
                _algorithm,
                am.FieldNotNullNotifier('string_slot')
            ]
        )
        for i in range(5):
            alg.iterate(FakeStorage(), messenger)

        client = BroClient(space, DebugClientDataProvider(), messenger)
        messages = client.get_notifications()
        print(messages)
        self.assertEqual(0, messages[0].payload['int_slot'])
        self.assertEqual(3, messages[1].payload['int_slot'])

    def test_storage(self):
        def _algorithm(space: SimpleSpace):
            space.int_slot.current_value = space.int_slot.history.first_or_default(-1)+1
            space.string_slot.current_value = 'a' + str(space.int_slot.current_value)

        storage = Sql.memory().storage()
        space = SimpleSpace()
        alg = BroAlgorithm(
            space,
            [_algorithm],
        )

        for i in range(5):
            alg.iterate(storage, FakeMessenger())

        client = BroClient(space, StorageClientDataProvider(space.get_name(), storage), FakeMessenger())
        df = pd.DataFrame(client.data_provider.pull())

        self.assertListEqual([0,1,2,3,4], list(df.int_slot))
        self.assertListEqual(['a0','a1','a2','a3','a4'], list(df.string_slot))


