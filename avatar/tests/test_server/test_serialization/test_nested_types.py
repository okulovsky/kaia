from dataclasses import dataclass, field
from unittest import TestCase
from avatar.server.serialization import to_json, from_json

@dataclass
class NestedDataclass:
    a: int = 1
    b: str = 'b'

class NestedTypesTestCase(TestCase):
    def test_json(self):
        @dataclass
        class Test1:
            c: NestedDataclass = field(metadata=dict(json=True))
            a: int = 1
        t = Test1(NestedDataclass())
        v = to_json(t, Test1)
        self.assertEqual({'c': {'a': 1, 'b': 'b'}, 'a': 1}, v)
        r = from_json(v, Test1)
        self.assertIsInstance(r.c, NestedDataclass)

    def test_jsonpickle(self):
        @dataclass
        class Test1:
            c: NestedDataclass
            a: int = 1
        t = Test1(NestedDataclass())
        v = to_json(t, Test1)
        self.assertEqual(1, v['a'])
        self.assertEqual(1, v['c']['a'])
        self.assertEqual('b', v['c']['b'])
        self.assertTrue(v['c']['py/object'].endswith('NestedDataclass'))
        r = from_json(v, Test1)
        self.assertIsInstance(r.c, NestedDataclass)



