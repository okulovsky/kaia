from unittest import TestCase
from kaia.infra.comm import Sql
from kaia.bro.core import BroServer
from kaia.bro.amenities.sandbox import SinSpace
from kaia.bro.amenities.eaglesong import BroSkill
from kaia.eaglesong.core import Scenario, BotContext, Options, SelectedOption, Delete

class EaglesongUnitTest(TestCase):
    def test_eaglesong(self):
        space = SinSpace()
        algorithm = space.create_algorithm()

        file = 'sample'
        conn = Sql.file(file, True)
        storage = conn.storage()
        messenger = conn.messenger()
        server = BroServer([algorithm], pause_in_milliseconds=50)
        server.run_in_multiprocess(storage, messenger)

        skill = BroSkill.generate_skill_for_server(server, storage, messenger)
        (Scenario(lambda: BotContext(123), skill, printing=Scenario.default_printing)
         .send('/start')
         .check(Options)
         .send(SelectedOption('sin'))
         .check(Delete, Options)
         .send(SelectedOption('cosine'))
         .check(Delete, Options)
         .send(SelectedOption('True'))
         .send(SelectedOption('←'))
         .validate()
         )
        print(messenger.read())

        (Scenario(lambda: BotContext(123), skill, printing=Scenario.default_printing)
         .send('/start')
         .check(Options)
         .send(SelectedOption('sin'))
         .check(Delete, Options)
         .send(SelectedOption('amplitude'))
         .check(Delete, str)
         .send('6.5')
         .preview()
         )

        data = messenger.read()
        self.assertEqual(2, len(data))
        self.assertListEqual(data[0].tags, ['to','sin','set_field','cosine'])
        self.assertEqual(data[0].payload, True)
        self.assertListEqual(data[1].tags, ['to','sin','set_field','amplitude'])

