import time

from avatar.server import AvatarApi, AvatarServerSettings, MessagingComponent, GenericMessage
from avatar.daemon import TextCommand, ImageCommand
from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.server.messaging_component.store import SqlMessageStore, InMemoryStore, CompositeStore



class AvatarApiTestCase(TestCase):
    def test_simple(self):
        with Loc.create_test_file() as file_name:
            settings = AvatarServerSettings(components=(
                MessagingComponent(file_name),
            ))
            with AvatarApi.Test(settings) as api:
                for i in range(5):
                    msg = GenericMessage(dict(index=i))
                    msg.envelop.id = str(i)
                    api.messaging.add('test', msg)
                messages = api.messaging.get()
                print(messages)
                self.assertEqual(5, len(messages))
                for i, m in enumerate(messages):
                    self.assertEqual(str(i), m.envelop.id)
                    self.assertEqual(i, m.payload['index'])

    def test_retrieval(self):
        factories = {
            'sql': SqlMessageStore,
            'in_memory': InMemoryStore.Factory(1000),
            'composite': CompositeStore.Factory(2),
        }

        for name, factory in factories.items():
            with self.subTest(name=name):
                with Loc.create_test_file() as file_name:
                    settings = AvatarServerSettings(components=(
                        MessagingComponent(file_name, store_factory=factory),
                    ))
                    with AvatarApi.Test(settings) as api:
                        for session in ['a', 'b']:
                            for i in range(5):
                                msg = GenericMessage(dict(index=i, session = session))
                                msg.envelop.id = session+str(i)
                                api.messaging.add(session, msg)

                        if name != 'in_memory':
                            self.assertEqual(
                                10,
                                len(api.messaging.get(None, None, None))
                            )

                            self.assertEqual(
                                5,
                                len(api.messaging.get('a', None, None))
                            )

                        self.assertEqual(
                            3,
                            len(api.messaging.get('a', 'a1', None))
                        )

                        self.assertEqual(
                            2,
                            len(api.messaging.get('a', 'a1', 2))
                        )

    def test_times(self):
        with Loc.create_test_file() as file_name:
            settings = AvatarServerSettings(components=(
                MessagingComponent(file_name),
            ))
            with AvatarApi.Test(settings) as api:
                N = 100
                write_begin = time.monotonic()
                for i in range(N):
                    api.messaging.add('test', GenericMessage(dict(index=i)))
                write_time = (time.monotonic() - write_begin)/N


                read_begin = time.monotonic()
                last = None
                while True:
                    result = api.messaging.get(last_message_id=last, count=1)
                    if len(result) == 0:
                        break
                    last = result[-1].envelop.id
                read_time = (time.monotonic() - read_begin)/N

                self.assertLess(write_time, 0.05)
                self.assertLess(read_time, 0.03)

    def test_exception_on_non_unique(self):
        with Loc.create_test_file() as file_name:
            settings = AvatarServerSettings(components=(
                MessagingComponent(file_name),
            ))
            with AvatarApi.Test(settings) as api:
                message = GenericMessage(dict())
                api.messaging.add('test', message)
                with self.assertRaises(Exception):
                    api.messaging.add('test', message)

    def test_cleanup(self):
        with Loc.create_test_file() as file_name:
            settings = AvatarServerSettings(components=(
                MessagingComponent(
                    file_name,
                    cleanup_time_in_seconds_to_message_types={0:(ImageCommand,)}
                ),
            ))
            with AvatarApi.Test(settings) as api:
                api.messaging.add('test', ImageCommand('test'))
                api.messaging.add('test', TextCommand('test'))
                result = api.messaging.get('test')
                self.assertEqual(1, len(result))
                self.assertIsInstance(result[0], TextCommand)








