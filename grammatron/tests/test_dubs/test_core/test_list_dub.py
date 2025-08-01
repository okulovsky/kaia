from grammatron.tests.common import *

inner = CardinalDub(100)

class ListDubTestCase(TestCase):
    def test_tostr(self):
        dub = ListDub(inner)
        self.assertEqual(dub.word_if_empty, dub.to_str(()))
        self.assertEqual("one and two", dub.to_str((1,2)))
        self.assertEqual("one, two and three", dub.to_str((1, 2, 3)))

        dub = ListDub(inner, separator='; ', last_separator=None, word_if_empty=None)
        self.assertRaises(Exception, lambda: dub.to_str(()))
        self.assertEqual("one; two", dub.to_str((1,2)))
        self.assertEqual("one; two; three", dub.to_str((1, 2, 3)))

    def test_parse(self):
        dub = ListDub(inner)
        run_regex_integration_test(
            self,
            dub,
            [
                (),
                (1,),
                (1,2),
                (1,2,3)
            ]
        )



