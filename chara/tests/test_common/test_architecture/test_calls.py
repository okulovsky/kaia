from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import Chara


def function(x: int) -> int:
    call_1 = Chara.call(another_function)(x,3)
    call_2 = Chara.call(another_function)(x,4)
    return call_1 + call_2

def another_function(x, y):
    return x*y



class CharaCallsTestCase(TestCase):
    def test_all(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            result = Chara.call(function)(3)
            self.assertEqual(21, result)
            self.assertEqual(21, Chara.previous.result)

            files = list(sorted(str(c.relative_to(folder)) for c in folder.glob('**/*')))
            self.assertEqual(
                ['.log',
                 '000-another_function',
                 '000-another_function/.log',
                 '000-another_function/result',
                 '001-another_function',
                 '001-another_function/.log',
                 '001-another_function/result',
                 'result',
                 ], files
            )




