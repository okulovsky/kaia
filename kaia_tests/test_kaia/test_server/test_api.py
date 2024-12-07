from kaia.kaia.server.api import KaiaApi, Bus
from unittest import TestCase
from kaia.infra import Loc

class KaiaApiTestCase(TestCase):
    def test_db(self):
        with Loc.create_temp_file('tests/kaia_api_test','db') as db_file:
            api = KaiaApi(Bus(db_file), '')
            api.add_image('test_image')
            api.add_sound('test_sound')

            updates = api.pull_updates()
            for u in updates:
                print(u.payload, type(u.payload))
