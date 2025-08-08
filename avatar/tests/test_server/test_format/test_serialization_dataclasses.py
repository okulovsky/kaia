from typing import Optional
from dataclasses import dataclass
from pstats import FunctionProfile
from unittest import TestCase
from avatar.server.format import Format
import json
from pprint import pprint

@dataclass
class C:
    a: int
    b: str
    c: Optional['C'] = None
    d: Optional[FunctionProfile] = None

class DataClassSerializationTestCase(TestCase):
    def check(self, value, _type):
        js = Format.to_json(value, _type)
        new_value = Format.from_json(js, _type)
        self.assertNotIn('@base64', json.dumps(js))
        if _type is type:
            self.assertIsInstance(value, _type)
        return js, new_value

    def test_dataclass(self):
        js, v = self.check(C(1,'b'), C)
        self.assertDictEqual({'a': 1, 'b': 'b', 'c': None, 'd': None}, js)
        self.assertEqual(1, v.a)
        self.assertEqual('b', v.b)
        self.assertIsNone(v.c)
        self.assertIsNone(v.d)

    def test_dataclass_nested(self):
        js, v = self.check(C(1,'b', C(2, 'd'), FunctionProfile('x',1,2,3,4,'y',5)), C)
        self.assertEqual({'a': 1, 'b': 'b', 'c': {'a': 2, 'b': 'd', 'c': None, 'd': None}, 'd': {'ncalls': 'x', 'tottime': 1, 'percall_tottime': 2, 'cumtime': 3, 'percall_cumtime': 4, 'file_name': 'y', 'line_number': 5}}, js)
        self.assertIsInstance(v.c, C)
        self.assertIsInstance(v.d, FunctionProfile)

    def test_tuple(self):
        js, v = self.check((C(1,'b'), None, C(2,'c')), tuple[C|None,...])
        self.assertEqual([{'a': 1, 'b': 'b', 'c': None, 'd': None}, None, {'a': 2, 'b': 'c', 'c': None, 'd': None}], js)
        self.assertIsInstance(v, tuple)
        self.assertIsInstance(v[0], C)
        self.assertIsInstance(v[2], C)



