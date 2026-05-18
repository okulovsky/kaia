import shutil
from chara.voice_clone.distillation.dataset.algorithm_annotation_step import algorithm_annotation_step
from chara.voice_clone.distillation.dataset.common import AnnotationCase
from chara.voice_clone.distillation.dataset.prepare_sententes import prepare_sentences
from chara.voice_clone.distillation.dataset import Corpus
from unittest import TestCase
from chara.common import Language, Chara
from foundation_kaia.misc import Loc
from pathlib import Path
import pickle


def create_data_pkl():
    with Loc.create_test_folder() as folder:
        corpus = Corpus([], 1000)
        Chara.start(folder)
        data = Chara.call(prepare_sentences)(Language.English().upsampling_dataset_reader()[:10], corpus,
                                             Language.English())
        (Path(__file__).parent / 'data.pkl').write_bytes(pickle.dumps(data))


def _mock(case: AnnotationCase):
    return 'YES' if case.text[0]<'F' else 'NO'


class AlgorithmAnnotationStepTestCase(TestCase):
    def test_annotation_step(self):
        data = pickle.loads((Path(__file__).parent / 'data.pkl').read_bytes())
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            result = Chara.call(algorithm_annotation_step)(data, [], 5, mock_annotation=_mock)
            self.assertEqual(5, len(result))
            self.assertEqual(
                ['1fff32630723f6501097', '6079e80576757dac27dd', 'f87be36d15722bdf73d1', '65d2f0b712347bb1875e', 'bdbd76dd282dba0d59e2'],
                [c.id for c in result]
            )
            self.assertEqual(
                [False, True, True, False, False],
                [c.accepted for c in result]
            )
            shutil.rmtree(folder)
            Chara.start(folder)

            result_1 = Chara.call(algorithm_annotation_step)(data, result, 5, mock_annotation=_mock)
            self.assertEqual(
                ['df109500655f2e012882', '2303ad05b81d95c9dff9', 'bb00d82750e393d250c6', '547f57ebc820340e9dbc', '3b897fac599aa86eddf3'],
                [c.id for c in result_1]
            )











