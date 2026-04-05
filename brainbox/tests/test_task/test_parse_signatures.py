from unittest import TestCase
from brainbox.deciders.utils.hello_brainbox.api import HelloBrainBox, HelloBrainBoxTaskBuilder
from brainbox.deciders.utils.hello_brainbox.app.model import HelloBrainBoxModelSpec
from brainbox.framework.task.entry_point import _parse_signatures_and_ctor


class ParseSignaturesAndCtorTestCase(TestCase):
    def setUp(self):
        self.sigs, self.ctor = _parse_signatures_and_ctor(HelloBrainBox, [])

    def test_signatures(self):
        # All signatures carry the correct decider name
        for sig in self.sigs.values():
            self.assertEqual('HelloBrainBox', sig.decider)

        # Basic endpoint from IHelloBrainBox
        self.assertIn('sum', self.sigs)
        sum_args = {a.name: a for a in self.sigs['sum'].signature.proper_arguments}
        self.assertIn('a', sum_args)
        self.assertIn('b', sum_args)

        # Generic-parameter endpoint from IModelInstallingSupport[HelloBrainBoxModelSpec]:
        # model_spec: TModelSpec must be resolved to HelloBrainBoxModelSpec
        self.assertIn('download_model', self.sigs)
        download_args = {a.name: a for a in self.sigs['download_model'].signature.proper_arguments}
        self.assertIn('model_spec', download_args)
        resolved_type = download_args['model_spec'].annotation.types[0].self.type
        self.assertIs(HelloBrainBoxModelSpec, resolved_type)

    def test_ctor(self):
        instance = self.ctor()
        self.assertIsInstance(instance, HelloBrainBoxTaskBuilder)

    def test_ordering_token(self):
        sigs, _ = _parse_signatures_and_ctor(HelloBrainBox, ['text', 'model'])
        self.assertEqual({'text': 0, 'model': 1}, sigs['voiceover'].argument_to_ordering_token_position)
        # other methods share the same dict but their args don't overlap — just verify it's assigned
        self.assertEqual({'text': 0, 'model': 1}, sigs['sum'].argument_to_ordering_token_position)
