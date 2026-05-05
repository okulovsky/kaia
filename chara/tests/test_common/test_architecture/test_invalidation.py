from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import Chara

def function(x):
    call_1 = Chara.call(function_1)(x,3)
    call_2 = Chara.call(function_1)(x,4)
    return call_1 + call_2 + x

def function_1(x, y):
    call_1 = Chara.call(function_2)(x)
    call_2 = Chara.call(function_2)(y)
    return call_1 * call_2

def function_2(x):
    return x+1


class CharaCallsTestCase(TestCase):
    def test_all(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            result = Chara.call(function)(3)
            self.assertEqual(39, result)

            for c in sorted(str(c.relative_to(folder)) for c in folder.glob('**/*')):
                print(c)

            Chara.start(folder)
            Chara.invalidate_self('')
            result = Chara.call(function)(4)
            self.assertEqual(40, result)

            Chara.start(folder)
            with self.assertRaises(ValueError):
                Chara.invalidate_down('000_fun')
            Chara.invalidate_down('000-function_1/001-function_2')
            result = Chara.call(function)(4)
            self.assertEqual(45, result)


            Chara.start(folder)
            Chara.invalidate_down('')
            result = Chara.call(function)(4)
            self.assertEqual(49, result)


