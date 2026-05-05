from unittest import TestCase
from chara.common import Chara
from chara.common.architecture.result_handling import ResultType
from foundation_kaia.misc import Loc


def _run_phases(folder):
    @Chara.phase
    def step_no_brackets():
        return 1

    @Chara.phase()
    def step_empty_brackets():
        return 2

    @Chara.phase(ResultType.Json)
    def step_with_result_type():
        return 3


class PhaseTestCase(TestCase):
    def test_phase_no_brackets(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)

            @Chara.phase
            def my_step():
                return 30

            self.assertEqual(30, Chara.previous.result)

    def test_phase_empty_brackets(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)

            @Chara.phase()
            def my_step():
                return 30

            self.assertEqual(30, Chara.previous.result)

    def test_phase_with_result_type(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)

            @Chara.phase(ResultType.Json)
            def my_step():
                return 30

            self.assertEqual(30, Chara.previous.result)

    def test_phase_names_from_function(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            Chara.call(_run_phases)(folder)
            files = sorted(str(c.relative_to(folder)) for c in folder.glob('**/*') if not c.name.startswith('.'))
            self.assertIn('000-step_no_brackets', files)
            self.assertIn('001-step_empty_brackets', files)
            self.assertIn('002-step_with_result_type', files)
