import time
from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.daemon import *
from kaia.tests.helper import Helper
from avatar.messaging.amenities import ThreadCollection
from yo_fluq import Query



class FacelessTestCase(TestCase):
    def test_initialization_event(self):
        with Loc.create_test_folder(dont_delete=True) as folder:
            helper = Helper(folder, self)
            with helper.app.get_fork_app(None):
                helper.client.initialize()
                helper.client.put(InitializationEvent())
                reaction = helper.parse_reaction(TextCommand)
                self.assertFalse(Query.en(reaction).where(lambda z: isinstance(z, ExceptionEvent)).any())
