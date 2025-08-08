import time

from avatar.server import AvatarApi, AvatarServerSettings, MessagingComponent
from unittest import TestCase
from foundation_kaia.misc import Loc

class AvatarApiTestCase(TestCase):
    def test_simple(self):
        with Loc.create_test_file() as file_name:
            settings = AvatarServerSettings(components=(
                MessagingComponent(file_name),
            ))
            with AvatarApi.Test(settings) as api:
                for i in range(5):
                    api.messaging.add('test', None, dict(id=str(i)), dict(index=i))
                messages = api.messaging.get()
                print(messages)
                self.assertEqual(5, len(messages))
                for i, m in enumerate(messages):
                    self.assertEqual(str(i), m['envelop']['id'])
                    self.assertEqual(i, m['payload']['index'])

    def test_retrieval(self):
        with Loc.create_test_file() as file_name:
            settings = AvatarServerSettings(components=(
                MessagingComponent(file_name),
            ))
            with AvatarApi.Test(settings) as api:
                for session in ['a', 'b']:
                    for i in range(5):
                        api.messaging.add('test', session, dict(id=session+str(i)), dict(index=i, session = session))

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
                    api.messaging.add('test', None, {}, dict(index=i))
                write_time = (time.monotonic() - write_begin)/N


                read_begin = time.monotonic()
                last = None
                while True:
                    result = api.messaging.get(last_message_id=last, count=1)
                    if len(result) == 0:
                        break
                    last = result[-1]['envelop']['id']
                read_time = (time.monotonic() - read_begin)/N

                self.assertLess(write_time, 0.02)
                self.assertLess(read_time, 0.01)






