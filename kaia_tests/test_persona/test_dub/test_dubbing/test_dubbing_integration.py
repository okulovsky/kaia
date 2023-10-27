from kaia.persona.dub.languages.en import *
from demos.persona.intents import Intents
from unittest import TestCase
from kaia.brainbox import BrainBox
from kaia.brainbox.core.testing import run_service
from kaia.brainbox.deciders.tortoise_tts import FakeDubDecider, DubCollector, FakeDubCollectorProcessor
import jsonpickle, json
import pandas as pd


class DubbingCycleTestCase(TestCase):
    def get_sequences(self, templates):
        box = BrainBox()
        tc = DubbingTaskCreator()
        sequences = tc.fragment(get_predefined_dubs(), templates, box.settings.tortoise_tts.test_voice)
        return sequences

    def run_service(self, sequences, run_real_server = False, to_lowercase = False):
        tc = DubbingTaskCreator()
        if run_real_server:
            dub_and_cut_tasks = tc.create_dub_and_cut_tasks(sequences)

            bb_tasks = tc.create_tasks(dub_and_cut_tasks, 'fake', 'dub', 'test_batch')
            results, log = run_service(bb_tasks, dict(fake=FakeDubDecider(), DubCollector=DubCollector(FakeDubCollectorProcessor())))

            for r in results:
                if not r.success:
                    print(r.error)
                self.assertTrue(r.success)

            result = jsonpickle.loads(json.dumps(results[-1].result))
            self.assertEqual(0, len(result['errors']))
            return DubbingPack(result['records'])
        else:
            return DubbingPack(tc.create_mock_fragments(sequences, to_lowercase))


    def test_packs_merging(self):
        pd.options.display.width = None
        templates = Intents.get_templates()
        tc = DubbingTaskCreator()

        # Creating tasks for "almost all templates"
        seq_1 = self.get_sequences(templates[:-4])
        pack_1 = self.run_service(seq_1)

        # Created diff
        seq_full = self.get_sequences(templates)
        diff = tc.get_sequences_missing_from_pack(seq_full, pack_1)
        pack_2 = self.run_service(diff)

        pack_3 = pack_1.merge_with_latest(pack_2)
        due_fragments = tc.create_mock_fragments(seq_full)
        self.assertEqual(len(pack_3.fragments), len(due_fragments))
        self.assertListEqual(
            list(sorted(p.text for p in pack_3.fragments)),
            list(sorted(p.text for p in due_fragments)),
        )

    def test_optimization(self):
        tc = DubbingTaskCreator()
        templates = Intents.get_templates()
        seq_1 = self.get_sequences(templates)
        seq_2 = tc.optimize_sequences(seq_1)
        self.assertLess(len(seq_2), len(seq_1))
        due_fragments = tc.create_mock_fragments(seq_1)
        fragments = tc.create_mock_fragments(seq_2)
        self.assertEqual(len(due_fragments), len(fragments))
        self.assertListEqual(
            list(sorted(p.text for p in due_fragments)),
            list(sorted(p.text for p in fragments)),
        )

    def simplify(self, s):
        return s.replace(' ','').replace(',','').replace('.','')



    def test_decomposition(self):
        tc = DubbingTaskCreator()
        templates = Intents.get_templates()
        seq_1 = self.get_sequences(templates)
        pack_1 = self.run_service(seq_1, to_lowercase=True)
        dub = pack_1.create_dubber()
        ttools = TestingTools(templates)
        for s in ttools.samples:
            print(f'[DUBBING] {s.s}')
            dubbing = dub.decompose(s.s, s.intent_obj)
            result = ''.join(dubbing)
            self.assertEqual(self.simplify(s.s.lower()), self.simplify(result))




    def test_with_external_process(self):
        templates = Intents.get_templates()
        seq = self.get_sequences(templates)
        tc = DubbingTaskCreator()
        seq = tc.optimize_sequences(seq)
        pack = self.run_service(seq, run_real_server=True)
        dub = pack.create_dubber()
        ttools = TestingTools(templates)
        for s in ttools.samples:
            print(f'[DUBBING REAL] {s.s}')
            dubbing = dub.decompose(s.s, s.intent_obj)
            result = ''.join(dubbing)
            self.assertEqual(self.simplify(s.s), self.simplify(result))





